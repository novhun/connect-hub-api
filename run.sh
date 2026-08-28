#!/usr/bin/env bash
# ==============================================================================
#  Connect-Hub API Management & Server Runner
#  Handles: Virtualenv, requirements.txt, Alembic migrations, DB seeding,
#  and flexible server execution modes (dev/prod/test/check).
# ==============================================================================

set -e

# Change directory to the root of connect-hub-api
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ANSI Color Codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default Configurations
DEFAULT_PORT=8008
DEFAULT_HOST="0.0.0.0"
DEFAULT_WORKERS=4
AUTO_MIGRATE=true
AUTO_SEED=false
RELOAD=true
ACTION="dev"
MIGRATION_MSG=""

# Load .env variables if present
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

PORT="${PORT:-$DEFAULT_PORT}"
HOST="${HOST:-$DEFAULT_HOST}"

# ------------------------------------------------------------------------------
#  Helper Functions
# ------------------------------------------------------------------------------

print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "================================================================"
    echo "       🚀 CONNECT-HUB BACKEND API MANAGEMENT SYSTEM 🚀         "
    echo "================================================================"
    echo -e "${NC}"
}

print_help() {
    print_banner
    echo -e "${BOLD}USAGE:${NC}"
    echo "  ./run.sh [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${BOLD}COMMANDS:${NC}"
    echo -e "  ${GREEN}dev${NC} (default)          Run FastAPI development server with auto-reload"
    echo -e "  ${GREEN}prod${NC} / ${GREEN}start${NC}         Run FastAPI production server with multi-worker Uvicorn"
    echo -e "  ${GREEN}makemigrations [msg]${NC} Generate new Alembic migration revision (--autogenerate)"
    echo -e "  ${GREEN}migrate${NC}              Apply all pending Alembic database migrations (upgrade head)"
    echo -e "  ${GREEN}rollback${NC}             Rollback the last applied database migration (downgrade -1)"
    echo -e "  ${GREEN}heads${NC} / ${GREEN}current${NC}        Show current and latest Alembic migration versions"
    echo -e "  ${GREEN}seed${NC}                 Seed database with demo users, posts, groups, and stories"
    echo -e "  ${GREEN}install${NC}              Install or update all dependencies from requirements.txt"
    echo -e "  ${GREEN}check${NC}                Check environment, Python venv, dependencies & DB connection"
    echo -e "  ${GREEN}test${NC}                 Run pytest test suite"
    echo -e "  ${GREEN}clean${NC}                Remove Python cache, bytecode, and temp files"
    echo -e "  ${GREEN}help${NC}                 Show this help message"
    echo ""
    echo -e "${BOLD}OPTIONS:${NC}"
    echo "  -p, --port <port>       Set server port (default: 8008)"
    echo "  -h, --host <host>       Set server host (default: 0.0.0.0)"
    echo "  -w, --workers <num>     Set number of workers for production (default: 4)"
    echo "  --no-reload             Disable auto-reload in dev mode"
    echo "  --no-migrate            Skip auto-migration check before starting server"
    echo "  --seed                  Seed demo data on server startup"
    echo "  -m, --message <msg>     Migration message for makemigrations"
    echo "  --help                  Show this help message"
    echo ""
    echo -e "${BOLD}EXAMPLES:${NC}"
    echo "  ./run.sh                                    # Start dev server"
    echo "  ./run.sh dev --port 8080                    # Dev server on port 8080"
    echo "  ./run.sh prod --workers 4                   # Start production server"
    echo '  ./run.sh makemigrations "add new fields"    # Create auto-migration'
    echo "  ./run.sh migrate                            # Apply migrations"
    echo "  ./run.sh seed                               # Seed demo data"
    echo "================================================================"
}

# ------------------------------------------------------------------------------
#  1. Virtual Environment Setup & Activation
# ------------------------------------------------------------------------------
setup_venv() {
    VENV_PATH=""
    if [ -d ".venv" ]; then
        VENV_PATH=".venv"
    elif [ -d "venv" ]; then
        VENV_PATH="venv"
    fi

    if [ -z "$VENV_PATH" ]; then
        echo -e "${YELLOW}⚙️  Virtual environment not found. Creating .venv using python3...${NC}"
        python3 -m venv .venv
        VENV_PATH=".venv"
        echo -e "${GREEN}✅ Created virtual environment at .venv${NC}"
    fi

    # Activate Virtual Environment
    # shellcheck disable=SC1090
    source "${VENV_PATH}/bin/activate"
    echo -e "${GREEN}🐍 Activated Python Virtualenv:${NC} $(which python3)"
}

# ------------------------------------------------------------------------------
#  2. Check & Install Dependencies from requirements.txt
# ------------------------------------------------------------------------------
check_requirements() {
    if [ ! -f "requirements.txt" ]; then
        echo -e "${YELLOW}⚠️  No requirements.txt found.${NC}"
        return
    fi

    # Check if core package 'fastapi' and 'alembic' are installed
    if ! python3 -c "import fastapi, alembic, sqlalchemy, uvicorn" 2>/dev/null; then
        echo -e "${YELLOW}📦 Core dependencies missing. Installing from requirements.txt...${NC}"
        pip install --upgrade pip --quiet
        pip install -r requirements.txt
        echo -e "${GREEN}✅ Dependencies successfully installed.${NC}"
    else
        echo -e "${GREEN}📦 Python dependencies verified.${NC}"
    fi
}

force_install_requirements() {
    echo -e "${CYAN}📦 Installing/Updating all packages from requirements.txt...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ All requirements successfully installed.${NC}"
}

# ------------------------------------------------------------------------------
#  3. Alembic Database Migration Functions
# ------------------------------------------------------------------------------
run_makemigrations() {
    local msg="$1"
    if [ -z "$msg" ]; then
        msg="auto_update_$(date +%Y%m%d_%H%M%S)"
    fi
    echo -e "${CYAN}🔄 Generating Alembic autogenerate migration: \"$msg\"...${NC}"
    alembic revision --autogenerate -m "$msg"
    echo -e "${GREEN}✅ Migration file created in alembic/versions/${NC}"
}

run_migrate() {
    echo -e "${CYAN}🚀 Applying Alembic migrations (upgrade head)...${NC}"
    alembic upgrade head
    echo -e "${GREEN}✅ Database schema is up-to-date.${NC}"
}

run_rollback() {
    echo -e "${YELLOW}⏪ Rolling back last Alembic migration (downgrade -1)...${NC}"
    alembic downgrade -1
    echo -e "${GREEN}✅ Migration rollback complete.${NC}"
}

run_migration_status() {
    echo -e "${CYAN}📊 Current Migration Status:${NC}"
    echo "--------------------------------------------------"
    alembic current
    echo "--------------------------------------------------"
    echo -e "${CYAN}📌 Migration Heads:${NC}"
    alembic heads
}

# ------------------------------------------------------------------------------
#  4. Seed Data Function
# ------------------------------------------------------------------------------
# run_seed() {
#     if [ -f "scripts/seed_data.py" ]; then
#         echo -e "${CYAN}🌱 Seeding database with demo data...${NC}"
#         python3 scripts/seed_data.py
#         echo -e "${GREEN}✅ Database seeding complete.${NC}"
#     else
#         echo -e "${RED}❌ scripts/seed_data.py not found.${NC}"
#     fi
# }

# ------------------------------------------------------------------------------
#  5. System & Environment Health Check
# ------------------------------------------------------------------------------
run_check() {
    print_banner
    echo -e "${BOLD}🔍 Running System & Environment Checks...${NC}"
    echo ""
    echo -e "  🐍 Python:      $(python3 --version)"
    echo -e "  📦 Pip:         $(pip --version | awk '{print $1, $2}')"
    echo -e "  📂 Directory:   $(pwd)"
    echo -e "  🌐 Environment: ${APP_ENV:-development}"
    echo -e "  🔌 Host:Port:   ${HOST}:${PORT}"
    
    # Check Database Connection
    echo -e "\n${BOLD}🗄️ Checking Database Connection...${NC}"
    if python3 -c "
import asyncio
from app.core.database import async_engine
from sqlalchemy import text
async def test_conn():
    async with async_engine.connect() as conn:
        await conn.execute(text('SELECT 1'))
    print('  ✅ Database connection successful!')
asyncio.run(test_conn())
" 2>/dev/null; then
        echo -e "${GREEN}  ✅ Database connection: OK${NC}"
    else
        echo -e "${RED}  ❌ Failed to connect to database. Check DATABASE_URL in .env${NC}"
    fi

    echo -e "\n${BOLD}📊 Alembic Migration Status:${NC}"
    alembic heads || true
    echo ""
    echo -e "${GREEN}✨ System check complete.${NC}"
}

# ------------------------------------------------------------------------------
#  6. Parse Command Line Arguments
# ------------------------------------------------------------------------------

# Detect command if first argument doesn't start with -
if [[ "$1" =~ ^[a-zA-Z_]+$ ]]; then
    ACTION="$1"
    shift
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -w|--workers)
            DEFAULT_WORKERS="$2"
            shift 2
            ;;
        -m|--message)
            MIGRATION_MSG="$2"
            shift 2
            ;;
        --no-reload)
            RELOAD=false
            shift
            ;;
        --no-migrate)
            AUTO_MIGRATE=false
            shift
            ;;
        --seed)
            AUTO_SEED=true
            shift
            ;;
        --install)
            ACTION="install"
            shift
            ;;
        --help)
            print_help
            exit 0
            ;;
        *)
            if [ -z "$MIGRATION_MSG" ] && [[ "$ACTION" == "makemigrations" || "$ACTION" == "revision" ]]; then
                MIGRATION_MSG="$1"
                shift
            else
                echo -e "${RED}Unknown option: $1${NC}"
                print_help
                exit 1
            fi
            ;;
    esac
done

# ------------------------------------------------------------------------------
#  Main Execution Routing
# ------------------------------------------------------------------------------

setup_venv

case "$ACTION" in
    help)
        print_help
        exit 0
        ;;
    install)
        force_install_requirements
        exit 0
        ;;
    makemigrations|revision)
        check_requirements
        run_makemigrations "$MIGRATION_MSG"
        exit 0
        ;;
    migrate|upgrade)
        check_requirements
        run_migrate
        exit 0
        ;;
    rollback|downgrade)
        check_requirements
        run_rollback
        exit 0
        ;;
    heads|current|history)
        check_requirements
        run_migration_status
        exit 0
        ;;
    seed)
        check_requirements
        run_seed
        exit 0
        ;;
    check)
        check_requirements
        run_check
        exit 0
        ;;
    test)
        check_requirements
        echo -e "${CYAN}🧪 Running pytest suite...${NC}"
        pytest
        exit 0
        ;;
    clean)
        echo -e "${YELLOW}🧹 Cleaning Python bytecode and cache files...${NC}"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        rm -rf .pytest_cache 2>/dev/null || true
        echo -e "${GREEN}✅ Clean complete.${NC}"
        exit 0
        ;;
    dev)
        print_banner
        check_requirements

        # Run auto-migration before dev server if enabled
        if [ "$AUTO_MIGRATE" = true ]; then
            run_migrate
        fi

        # Seed if requested
        if [ "$AUTO_SEED" = true ]; then
            run_seed
        fi

        echo -e "${CYAN}🚀 Starting FastAPI Development Server on http://${HOST}:${PORT}...${NC}"
        echo -e "${BLUE}📖 API Docs: http://localhost:${PORT}/docs${NC}"
        echo "----------------------------------------------------------------"
        
        if [ "$RELOAD" = true ]; then
            exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
        else
            exec uvicorn app.main:app --host "$HOST" --port "$PORT"
        fi
        ;;
    prod|start)
        print_banner
        check_requirements

        # Run auto-migration before prod server if enabled
        if [ "$AUTO_MIGRATE" = true ]; then
            run_migrate
        fi

        echo -e "${CYAN}🚀 Starting FastAPI Production Server on http://${HOST}:${PORT} (${DEFAULT_WORKERS} workers)...${NC}"
        echo "----------------------------------------------------------------"
        exec uvicorn app.main:app --host "$HOST" --port "$PORT" --workers "$DEFAULT_WORKERS"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $ACTION${NC}"
        print_help
        exit 1
        ;;
esac
