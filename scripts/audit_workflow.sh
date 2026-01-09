#!/bin/bash

# ==============================================================================
# Google Antigravity: Universal Orchestrator
# Version: 3.0 (Universal Orchestrator + Holmesian Cognitive Core)
# Architecture: OODA Loop with Intent-Based Probabilistic Routing
# ==============================================================================
#
# This script invokes the Universal Orchestrator which implements:
# - OODA Loop: Observe → Orient → Decide → Act (continuous)
# - Intent-Based Routing: Natural language → capability mapping
# - Probabilistic Module Selection: U(M|T,C) = P(Success) × V - Cost
# - Self-Calibration: Runtime parameter tuning
# - Holmesian Cognitive Core: Mind Palace, Brain Attic, Bayesian Engine
#
# ==============================================================================

# Strict error handling
set -e
set -o pipefail

# Configuration Environment Variables
export SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export FRAMEWORK_ROOT="$(dirname "$SCRIPT_DIR")"

# Target Directory Resolution (set later by argument parsing)
export TARGET_DIR="${TARGET_DIR:-$(pwd)}"

export OUTPUT_DIR="${TARGET_DIR}/antigravity_output"
export REPORTS_DIR="${TARGET_DIR}/antigravity_reports"
export LOG_DIR="${TARGET_DIR}/antigravity_logs"

# Python path setup
export PYTHONPATH="${FRAMEWORK_ROOT}:${PYTHONPATH:-}"

# Color codes for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Logging function
log() {
    local level="$1"
    local msg="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local color="$NC"

    case "$level" in
        "INFO") color="$BLUE" ;;
        "SUCCESS") color="$GREEN" ;;
        "WARN") color="$YELLOW" ;;
        "ERROR") color="$RED" ;;
        "OODA") color="$MAGENTA" ;;
    esac

    echo -e "${color}[${level}]${NC} ${msg}"
    if [[ -d "$LOG_DIR" ]]; then
        echo "[${timestamp}][${level}] ${msg}" >> "$LOG_DIR/orchestrator.log"
    fi
}

# Print banner
print_banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    GOOGLE ANTIGRAVITY v3.0                                ║${NC}"
    echo -e "${CYAN}║                  UNIVERSAL ORCHESTRATOR                                   ║${NC}"
    echo -e "${CYAN}║         Holmesian Cognitive Architecture + OODA Loop                      ║${NC}"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║                                                                           ║${NC}"
    echo -e "${CYAN}║   'From software that works to software that thinks.'                     ║${NC}"
    echo -e "${CYAN}║                                                                           ║${NC}"
    echo -e "${CYAN}║   Components:                                                             ║${NC}"
    echo -e "${CYAN}║   ├─ Intent Recognition Engine (Vector-Space Clustering)                  ║${NC}"
    echo -e "${CYAN}║   ├─ Probabilistic Router (POMDP Utility Calculation)                     ║${NC}"
    echo -e "${CYAN}║   ├─ Context Manager (Tiered Context Stack)                               ║${NC}"
    echo -e "${CYAN}║   ├─ Self-Calibration Engine (Meta-Learning)                              ║${NC}"
    echo -e "${CYAN}║   └─ Agents: Watson → Sherlock → Moriarty → Mycroft                       ║${NC}"
    echo -e "${CYAN}║                                                                           ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Usage
usage() {
    echo "Usage: $0 [OPTIONS] <target_directory>"
    echo ""
    echo "OPTIONS:"
    echo "  --intent <string>       Natural language intent (default: 'Perform comprehensive security audit')"
    echo "  --scope <pattern>       Target scope pattern (default: '*.sol')"
    echo "  --risk <level>          Risk tolerance: minimal|low|medium|high|maximum (default: medium)"
    echo "  --timeout <seconds>     Timeout in seconds (default: 3600)"
    echo "  --output <file>         Output file for results (default: auto-generated)"
    echo "  --mode <mode>           Mode: full|quick|deep (default: full)"
    echo "  --legacy                Run legacy 4-phase pipeline instead of OODA loop"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 ./contracts"
    echo "  $0 --intent 'Check for reentrancy vulnerabilities' ./contracts"
    echo "  $0 --risk high --mode deep ./defi-protocol"
    echo ""
}

# Initialize directories
init_system() {
    mkdir -p "$OUTPUT_DIR" "$REPORTS_DIR" "$LOG_DIR"
    log "INFO" "Initializing Universal Orchestrator..."
    log "INFO" "Target: $TARGET_DIR"
    log "INFO" "Output: $OUTPUT_DIR"
}

# Check dependencies
check_dependencies() {
    log "INFO" "Checking dependencies..."
    
    # Python check
    if ! command -v python3 >/dev/null 2>&1; then
        log "ERROR" "Python 3 is required but not found."
        exit 1
    fi
    
    # Check orchestrator module
    if ! python3 -c "from agents.universal_orchestrator import UniversalOrchestrator" 2>/dev/null; then
        log "ERROR" "Universal Orchestrator module not found."
        log "INFO" "Ensure PYTHONPATH includes: $FRAMEWORK_ROOT"
        exit 1
    fi
    
    log "SUCCESS" "All dependencies satisfied."
}

# Run Universal Orchestrator (OODA Loop)
run_orchestrator() {
    local intent="$1"
    local scope="$2"
    local risk="$3"
    local timeout="$4"
    local output_file="$5"
    local context_file="$6"
    
    log "OODA" "Starting OODA Loop..."
    log "OODA" "Intent: $intent"
    log "OODA" "Scope: $scope"
    log "OODA" "Risk Tolerance: $risk"
    echo ""
    
    python3 -m agents.universal_orchestrator \
        --intent "$intent" \
        --scope "$scope" \
        --risk-tolerance "$risk" \
        --timeout "$timeout" \
        --output "$output_file" \
        --context "$context_file"
    
    echo ""
    log "SUCCESS" "OODA Loop complete."
    log "INFO" "Results saved to: $output_file"
}

# Legacy 4-Phase Pipeline (for backward compatibility)
run_legacy_pipeline() {
    local context_arg=""
    if [ -n "$1" ]; then
        context_arg="--context $1"
    fi

    log "WARN" "Running legacy 4-phase pipeline..."
    
    # Phase 1: Watson
    log "INFO" ">>> PHASE 1: WATSON (Perception) <<<"
    # shellcheck disable=SC2086
    python3 "$FRAMEWORK_ROOT/agents/watson.py" \
        --action observe \
        --input "$TARGET_DIR" \
        --output "$OUTPUT_DIR/observations.json" \
        $context_arg \
        2>> "$LOG_DIR/watson.log" || true
    
    # Phase 2: Sherlock
    log "INFO" ">>> PHASE 2: SHERLOCK (Deduction) <<<"
    python3 "$FRAMEWORK_ROOT/agents/sherlock.py" \
        --action detect \
        --input "$OUTPUT_DIR/observations.json" \
        --output "$OUTPUT_DIR/findings.json" \
        $context_arg \
        2>> "$LOG_DIR/sherlock.log" || true
    
    # Phase 3: Moriarty
    log "INFO" ">>> PHASE 3: MORIARTY (Adversarial) <<<"
    python3 "$FRAMEWORK_ROOT/agents/moriarty.py" \
        --action exploit \
        --input "$OUTPUT_DIR/findings.json" \
        --output-dir "$OUTPUT_DIR/exploits" \
        2>> "$LOG_DIR/moriarty.log" || true
    
    # Phase 4: Mycroft
    log "INFO" ">>> PHASE 4: MYCROFT (Synthesis) <<<"
    python3 "$FRAMEWORK_ROOT/agents/mycroft.py" \
        --action report \
        --input "$OUTPUT_DIR/findings.json" \
        --output "$REPORTS_DIR/Antigravity_Report_$(date +%F).md" \
        2>> "$LOG_DIR/mycroft.log" || true
    
    log "SUCCESS" "Legacy pipeline complete."
}

# Main
main() {
    # Default values
    local intent="Perform comprehensive security audit"
    local scope="*.sol"
    local risk="medium"
    local timeout=3600
    local output_file=""
    local mode="full"
    local legacy=false
    local target=""
    local context_file=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --intent)
                intent="$2"
                shift 2
                ;;
            --scope)
                scope="$2"
                shift 2
                ;;
            --risk)
                risk="$2"
                shift 2
                ;;
            --timeout)
                timeout="$2"
                shift 2
                ;;
            --output)
                output_file="$2"
                shift 2
                ;;
            --mode)
                mode="$2"
                shift 2
                ;;
            --legacy)
                legacy=true
                shift
                ;;
            --context)
                context_file="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                log "ERROR" "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                target="$1"
                shift
                ;;
        esac
    done
    
    # Validate target
    if [[ -z "$target" ]]; then
        log "ERROR" "No target directory specified."
        usage
        exit 1
    fi
    
    if [[ ! -d "$target" ]]; then
        log "ERROR" "Target directory does not exist: $target"
        exit 1
    fi
    
    TARGET_DIR="$(cd "$target" && pwd)"
    OUTPUT_DIR="${TARGET_DIR}/antigravity_output"
    REPORTS_DIR="${TARGET_DIR}/antigravity_reports"
    LOG_DIR="${TARGET_DIR}/antigravity_logs"
    
    # Default output file
    if [[ -z "$output_file" ]]; then
        output_file="$OUTPUT_DIR/orchestrator_result_$(date +%F_%H%M%S).json"
    fi
    
    # Banner
    print_banner
    
    # Initialize
    init_system
    check_dependencies
    
    # Adjust based on mode
    case "$mode" in
        quick)
            timeout=300
            log "INFO" "Quick mode: timeout set to 5 minutes"
            ;;
        deep)
            timeout=7200
            risk="high"
            log "INFO" "Deep mode: timeout set to 2 hours, risk tolerance: high"
            ;;
        full)
            log "INFO" "Full mode: standard settings"
            ;;
        *)
            log "WARN" "Unknown mode: $mode, using full"
            ;;
    esac
    
    # Execute
    if [[ "$legacy" == true ]]; then
        run_legacy_pipeline "$context_file"
    else
        run_orchestrator "$intent" "$scope" "$risk" "$timeout" "$output_file" "$context_file"
    fi
    
    echo ""
    log "SUCCESS" ">>> AUDIT COMPLETE <<<"
    log "INFO" "Reports: $REPORTS_DIR"
    log "INFO" "Logs: $LOG_DIR"
    echo ""
}

# Run main
main "$@"

exit 0
