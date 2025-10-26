#!/bin/bash
# Health check script for Personal Finance Automation system
# Can be used standalone or by monitoring systems

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8080}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Exit codes
EXIT_SUCCESS=0
EXIT_WARNING=1
EXIT_CRITICAL=2
EXIT_UNKNOWN=3

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local service=$2
    local response

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC} $service is ${GREEN}healthy${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗${NC} $service is ${RED}unhealthy${NC} (HTTP $response)"
        return 1
    fi
}

# Function to check PostgreSQL
check_postgres() {
    if command -v pg_isready &> /dev/null; then
        if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" &> /dev/null; then
            echo -e "${GREEN}✓${NC} PostgreSQL is ${GREEN}accepting connections${NC}"
            return 0
        else
            echo -e "${RED}✗${NC} PostgreSQL is ${RED}not responding${NC}"
            return 1
        fi
    elif command -v docker &> /dev/null; then
        if docker compose exec -T postgres pg_isready &> /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} PostgreSQL is ${GREEN}accepting connections${NC}"
            return 0
        else
            echo -e "${RED}✗${NC} PostgreSQL is ${RED}not responding${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} PostgreSQL check ${YELLOW}skipped${NC} (no pg_isready or docker)"
        return 2
    fi
}

# Function to check Redis
check_redis() {
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &> /dev/null; then
            echo -e "${GREEN}✓${NC} Redis is ${GREEN}responding${NC}"
            return 0
        else
            echo -e "${RED}✗${NC} Redis is ${RED}not responding${NC}"
            return 1
        fi
    elif command -v docker &> /dev/null; then
        if docker compose exec -T redis redis-cli ping &> /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Redis is ${GREEN}responding${NC}"
            return 0
        else
            echo -e "${RED}✗${NC} Redis is ${RED}not responding${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} Redis check ${YELLOW}skipped${NC} (no redis-cli or docker)"
        return 2
    fi
}

# Function to check Docker containers
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠${NC} Docker check ${YELLOW}skipped${NC} (docker not found)"
        return 2
    fi

    local containers=$(docker compose ps -q 2>/dev/null | wc -l)
    local running=$(docker compose ps -q --status running 2>/dev/null | wc -l)

    if [ "$containers" -eq 0 ]; then
        echo -e "${RED}✗${NC} No Docker containers found"
        return 1
    elif [ "$running" -eq "$containers" ]; then
        echo -e "${GREEN}✓${NC} All Docker containers are ${GREEN}running${NC} ($running/$containers)"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Some containers are not running: ${YELLOW}$running/$containers${NC}"
        return 1
    fi
}

# Function to get system metrics
get_metrics() {
    echo -e "\n${CYAN}System Metrics:${NC}"

    # API response time
    if command -v curl &> /dev/null; then
        local response_time
        response_time=$(curl -s -o /dev/null -w "%{time_total}" "$API_URL/health" 2>/dev/null || echo "N/A")
        echo -e "  API Response Time: ${response_time}s"
    fi

    # Docker stats
    if command -v docker &> /dev/null; then
        echo -e "\n  Container Resources:"
        docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null | tail -n +2 | while read line; do
            echo "    $line"
        done
    fi
}

# Main health check
main() {
    echo -e "${CYAN}Personal Finance Automation - Health Check${NC}"
    echo -e "${CYAN}==========================================${NC}\n"

    local exit_code=$EXIT_SUCCESS

    # Check API
    if ! check_http "$API_URL/health" "API"; then
        exit_code=$EXIT_CRITICAL
    fi

    # Check PostgreSQL
    postgres_result=$(check_postgres; echo $?)
    if [ "$postgres_result" -eq 1 ]; then
        exit_code=$EXIT_CRITICAL
    elif [ "$postgres_result" -eq 2 ] && [ "$exit_code" -eq $EXIT_SUCCESS ]; then
        exit_code=$EXIT_WARNING
    fi

    # Check Redis
    redis_result=$(check_redis; echo $?)
    if [ "$redis_result" -eq 1 ]; then
        exit_code=$EXIT_CRITICAL
    elif [ "$redis_result" -eq 2 ] && [ "$exit_code" -eq $EXIT_SUCCESS ]; then
        exit_code=$EXIT_WARNING
    fi

    # Check Docker containers
    docker_result=$(check_docker; echo $?)
    if [ "$docker_result" -eq 1 ]; then
        exit_code=$EXIT_CRITICAL
    elif [ "$docker_result" -eq 2 ] && [ "$exit_code" -eq $EXIT_SUCCESS ]; then
        exit_code=$EXIT_WARNING
    fi

    # Show metrics if verbose mode
    if [ "${VERBOSE:-0}" -eq 1 ]; then
        get_metrics
    fi

    # Summary
    echo ""
    if [ "$exit_code" -eq $EXIT_SUCCESS ]; then
        echo -e "${GREEN}✓✓✓ All systems operational ✓✓✓${NC}"
    elif [ "$exit_code" -eq $EXIT_WARNING ]; then
        echo -e "${YELLOW}⚠⚠⚠ Some checks skipped or warnings ⚠⚠⚠${NC}"
    else
        echo -e "${RED}✗✗✗ System health check failed ✗✗✗${NC}"
    fi

    exit $exit_code
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose    Show detailed metrics"
            echo "  -h, --help       Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  API_URL          API base URL (default: http://localhost:8080)"
            echo "  POSTGRES_HOST    PostgreSQL host (default: localhost)"
            echo "  POSTGRES_PORT    PostgreSQL port (default: 5432)"
            echo "  REDIS_HOST       Redis host (default: localhost)"
            echo "  REDIS_PORT       Redis port (default: 6379)"
            echo ""
            echo "Exit codes:"
            echo "  0 - Success: All systems operational"
            echo "  1 - Warning: Some checks skipped"
            echo "  2 - Critical: Health check failed"
            echo "  3 - Unknown: Unexpected error"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit $EXIT_UNKNOWN
            ;;
    esac
done

# Run main function
main
