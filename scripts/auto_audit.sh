#!/bin/bash
#===============================================================================
#
#  AUTO AUDIT - Automated Security Audit Entry Point
#  ==================================================
#
#  Single command to audit any smart contract project:
#
#  Usage:
#    ./auto_audit.sh https://github.com/protocol/contracts
#    ./auto_audit.sh ./local-contracts
#    ./auto_audit.sh https://github.com/protocol/contracts --focus reentrancy
#
#  What it does:
#    1. Clones repo (if GitHub URL provided)
#    2. Analyzes project (framework, scope, protocol type)
#    3. Runs AI research phase
#    4. Executes full audit workflow (Watson → Sherlock → Moriarty → Mycroft)
#    5. Generates final report
#
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

#===============================================================================
# Configuration
#===============================================================================

CLONE_DIR="${ROOT_DIR}/targets"
OUTPUT_DIR="${ROOT_DIR}/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

#===============================================================================
# Functions
#===============================================================================

print_banner() {
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                       ║"
    echo "║   🔍 SHERLOCK AUTO AUDIT                                              ║"
    echo "║   ━━━━━━━━━━━━━━━━━━━━━━━━                                            ║"
    echo "║   Automated Smart Contract Security Auditing                          ║"
    echo "║   Powered by Holmesian Cognitive Architecture                         ║"
    echo "║                                                                       ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_step() {
    echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} ${GREEN}▶${NC} $1"
}

log_info() {
    echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} ${BLUE}ℹ${NC} $1"
}

log_warn() {
    echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} ${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} ${RED}✗${NC} $1"
}

log_success() {
    echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} ${GREEN}✓${NC} $1"
}

show_usage() {
    echo "Usage: $0 <target> [options]"
    echo ""
    echo "Target:"
    echo "  GitHub URL    https://github.com/owner/repo"
    echo "  Local path    ./contracts or /path/to/contracts"
    echo ""
    echo "Options:"
    echo "  --focus <area>      Focus on specific vulnerability type"
    echo "  --skip-research     Skip AI research phase"
    echo "  --skip-build        Skip building the project"
    echo "  --output <dir>      Custom output directory"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 https://github.com/aave/aave-v3-core"
    echo "  $0 ./my-contracts --focus reentrancy"
    echo "  $0 https://github.com/uniswap/v4-core --output ./audit-results"
}

is_github_url() {
    [[ "$1" =~ ^https?://github\.com/ ]]
}

clone_repo() {
    local url="$1"
    local repo_name
    
    # Extract repo name from URL
    repo_name=$(echo "$url" | sed 's|.*/||' | sed 's|\.git$||')
    
    local target_dir="${CLONE_DIR}/${repo_name}_${TIMESTAMP}"
    
    log_step "Cloning repository: ${repo_name}"
    mkdir -p "$CLONE_DIR"
    
    if git clone --depth 1 "$url" "$target_dir" 2>/dev/null; then
        log_success "Repository cloned to: $target_dir"
        echo "$target_dir"
    else
        log_error "Failed to clone repository"
        exit 1
    fi
}

analyze_project() {
    local project_dir="$1"
    local output_file="$2"
    
    log_step "Analyzing project structure..."
    
    python3 "${ROOT_DIR}/agents/project_analyzer.py" \
        --input "$project_dir" \
        --output "$output_file"
    
    if [ -f "$output_file" ]; then
        log_success "Project analysis complete"
        
        # Display summary
        local framework=$(jq -r '.framework' "$output_file")
        local protocol_type=$(jq -r '.protocol_type' "$output_file")
        local total_files=$(jq -r '.total_sol_files' "$output_file")
        local total_lines=$(jq -r '.total_lines' "$output_file")
        
        echo ""
        echo -e "  ${BLUE}Framework:${NC}     $framework"
        echo -e "  ${BLUE}Protocol:${NC}      $protocol_type"
        echo -e "  ${BLUE}Scope:${NC}         $total_files files, $total_lines lines"
        echo ""
    else
        log_error "Project analysis failed"
        exit 1
    fi
}

run_research() {
    local project_file="$1"
    local output_file="$2"
    
    log_step "Running AI research phase..."
    
    python3 "${ROOT_DIR}/agents/researcher.py" \
        --project "$project_file" \
        --output "$output_file"
    
    if [ -f "$output_file" ]; then
        log_success "Research phase complete"
        
        # Display summary
        local num_vulns=$(jq '.common_vulnerabilities | length' "$output_file")
        local focus_areas=$(jq -r '.audit_focus_areas | join(", ")' "$output_file")
        
        echo ""
        echo -e "  ${BLUE}Common Vulns:${NC}  $num_vulns identified"
        echo -e "  ${BLUE}Focus Areas:${NC}   $focus_areas"
        echo ""
    else
        log_warn "Research phase produced no output (continuing anyway)"
    fi
}

build_project() {
    local project_dir="$1"
    local project_file="$2"
    
    local build_cmd=$(jq -r '.build_command' "$project_file")
    
    if [ "$build_cmd" = "null" ] || [ -z "$build_cmd" ] || [[ "$build_cmd" == "#"* ]]; then
        log_info "No build command detected, skipping build"
        return 0
    fi
    
    log_step "Building project: $build_cmd"
    
    cd "$project_dir"
    if eval "$build_cmd" 2>/dev/null; then
        log_success "Project built successfully"
    else
        log_warn "Build failed (continuing anyway)"
    fi
    cd - > /dev/null
}

run_audit_workflow() {
    local project_dir="$1"
    local output_dir="$2"
    local research_file="$3"
    local intent="${4:-Comprehensive security audit}"
    
    log_step "Starting audit workflow..."
    
    # Use the existing audit_workflow.sh
    if [ -f "${SCRIPT_DIR}/audit_workflow.sh" ]; then
        "${SCRIPT_DIR}/audit_workflow.sh" \
            "$project_dir" \
            --output "${output_dir}/orchestrator_output.json" \
            --intent "$intent" \
            --context "$research_file"
    else
        log_warn "audit_workflow.sh not found, running agents directly"
        
        # Run agents directly
        log_step "Phase 1: Watson (Observation)"
        python3 "${ROOT_DIR}/agents/watson.py" --action observe \
            --input "$project_dir" \
            --output "${output_dir}/watson_observations.json" 2>/dev/null || true
        
        log_step "Phase 2: Sherlock (Deduction)"
        python3 "${ROOT_DIR}/agents/sherlock.py" --action analyze \
            --input "${output_dir}/watson_observations.json" \
            --output "${output_dir}/sherlock_findings.json" 2>/dev/null || true
        
        log_step "Phase 3: Moriarty (Exploitation)"
        python3 "${ROOT_DIR}/agents/moriarty.py" --action exploit \
            --input "${output_dir}/sherlock_findings.json" \
            --output "${output_dir}/moriarty_exploits.json" 2>/dev/null || true
        
        log_step "Phase 4: Mycroft (Synthesis)"
        python3 "${ROOT_DIR}/agents/mycroft.py" --action synthesize \
            --input "${output_dir}/moriarty_exploits.json" \
            --output "${output_dir}/report.md" 2>/dev/null || true
    fi
    
    log_success "Audit workflow complete"
}

generate_summary() {
    local output_dir="$1"
    local project_name="$2"
    
    log_step "Generating audit summary..."
    
    local summary_file="${output_dir}/AUDIT_SUMMARY.md"
    
    cat > "$summary_file" << EOF
# Audit Summary: ${project_name}

**Generated:** $(date)
**Framework:** Sherlock Holmesian Cognitive Architecture

## Files Generated

- \`project.json\` - Project analysis results
- \`research.json\` - AI research context
- \`watson_observations.json\` - Code observations
- \`sherlock_findings.json\` - Vulnerability findings
- \`moriarty_exploits.json\` - Exploit proofs
- \`report.md\` - Final audit report

## Quick Stats

$(if [ -f "${output_dir}/project.json" ]; then
    echo "- **Framework:** $(jq -r '.framework' "${output_dir}/project.json")"
    echo "- **Protocol Type:** $(jq -r '.protocol_type' "${output_dir}/project.json")"
    echo "- **Files in Scope:** $(jq -r '.total_sol_files' "${output_dir}/project.json")"
    echo "- **Lines of Code:** $(jq -r '.total_lines' "${output_dir}/project.json")"
fi)

## Next Steps

1. Review the findings in \`sherlock_findings.json\`
2. Check exploit proofs in \`moriarty_exploits.json\`
3. Read the full report in \`report.md\`
EOF

    log_success "Summary saved to: $summary_file"
}

#===============================================================================
# Main
#===============================================================================

main() {
    print_banner
    
    # Parse arguments
    local TARGET=""
    local FOCUS=""
    local SKIP_RESEARCH=false
    local SKIP_BUILD=false
    local CUSTOM_OUTPUT=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --focus)
                FOCUS="$2"
                shift 2
                ;;
            --skip-research)
                SKIP_RESEARCH=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --output)
                CUSTOM_OUTPUT="$2"
                shift 2
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                if [ -z "$TARGET" ]; then
                    TARGET="$1"
                fi
                shift
                ;;
        esac
    done
    
    if [ -z "$TARGET" ]; then
        log_error "No target specified"
        show_usage
        exit 1
    fi
    
    # Determine project directory
    local PROJECT_DIR
    local PROJECT_NAME
    
    if is_github_url "$TARGET"; then
        log_info "Detected GitHub URL"
        PROJECT_DIR=$(clone_repo "$TARGET")
        PROJECT_NAME=$(basename "$PROJECT_DIR" | sed 's/_[0-9]*$//')
    else
        if [ -d "$TARGET" ]; then
            PROJECT_DIR=$(cd "$TARGET" && pwd)
            PROJECT_NAME=$(basename "$PROJECT_DIR")
            log_info "Using local directory: $PROJECT_DIR"
        else
            log_error "Target not found: $TARGET"
            exit 1
        fi
    fi
    
    # Set up output directory
    if [ -n "$CUSTOM_OUTPUT" ]; then
        AUDIT_OUTPUT="$CUSTOM_OUTPUT"
    else
        AUDIT_OUTPUT="${OUTPUT_DIR}/${PROJECT_NAME}_${TIMESTAMP}"
    fi
    mkdir -p "$AUDIT_OUTPUT"
    
    log_info "Output directory: $AUDIT_OUTPUT"
    
    # Phase 1: Analyze project
    echo ""
    echo -e "${PURPLE}━━━ Phase 1: Project Analysis ━━━${NC}"
    analyze_project "$PROJECT_DIR" "${AUDIT_OUTPUT}/project.json"
    
    # Phase 2: AI Research
    if [ "$SKIP_RESEARCH" = false ]; then
        echo ""
        echo -e "${PURPLE}━━━ Phase 2: AI Research ━━━${NC}"
        run_research "${AUDIT_OUTPUT}/project.json" "${AUDIT_OUTPUT}/research.json"
    fi
    
    # Phase 3: Build project
    if [ "$SKIP_BUILD" = false ]; then
        echo ""
        echo -e "${PURPLE}━━━ Phase 3: Build Project ━━━${NC}"
        build_project "$PROJECT_DIR" "${AUDIT_OUTPUT}/project.json"
    fi
    
    # Phase 4: Run audit workflow
    echo ""
    echo -e "${PURPLE}━━━ Phase 4: Audit Workflow ━━━${NC}"
    local INTENT="Comprehensive security audit"
    if [ -n "$FOCUS" ]; then
        INTENT="Security audit focusing on ${FOCUS}"
    fi
    run_audit_workflow "$PROJECT_DIR" "$AUDIT_OUTPUT" "${AUDIT_OUTPUT}/research.json" "$INTENT"
    
    # Phase 5: Generate summary
    echo ""
    echo -e "${PURPLE}━━━ Phase 5: Summary ━━━${NC}"
    generate_summary "$AUDIT_OUTPUT" "$PROJECT_NAME"
    
    # Done!
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                       ║${NC}"
    echo -e "${GREEN}║   ✅ AUDIT COMPLETE                                                   ║${NC}"
    echo -e "${GREEN}║                                                                       ║${NC}"
    echo -e "${GREEN}║   Results saved to:                                                   ║${NC}"
    echo -e "${GREEN}║   ${AUDIT_OUTPUT}${NC}"
    echo -e "${GREEN}║                                                                       ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Run main
main "$@"
