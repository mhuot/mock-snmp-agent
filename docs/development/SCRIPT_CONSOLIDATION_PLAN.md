# Script Consolidation Plan

## Current State Analysis
- 17 Python scripts in repository (updated count)
- Significant functional overlap in testing scripts
- All scripts are documented but maintenance burden is high
- Recent additions include utility scripts that provide specific functionality

## Consolidation Strategy

### Scripts to Keep (Core Functionality)
1. **`mock_snmp_agent.py`** - Main entry point ✓
2. **`run_api_tests.py`** - API test runner ✓
3. **`config.py`** - Configuration management ✓
4. **`healthcheck.py`** - Docker health check ✓
5. **`cleanup_ports.py`** - Port cleanup utility ✓ *(new utility script)*

### Scripts to Consolidate

#### Performance Testing (Merge 3 → 1)
**Keep:** `performance_test.py` (most comprehensive)
**Remove:**
- `quick_performance_test.py` (redundant - subset of performance_test.py)
- `simple_prd_test.py` (redundant - similar functionality)

**Action:** Enhance `performance_test.py` with quick test options via CLI flags

#### Basic Testing (Merge 2 → 1)
**Keep:** `test_prd_requirements.py` (more comprehensive)
**Remove:**
- `test_basic.py` (redundant - basic subset of test_prd_requirements.py)

**Action:** Ensure `test_prd_requirements.py` includes all basic test functionality

#### Validation (Merge 2 → 1)
**Keep:** `validate_prd_compliance.py` (comprehensive validation)
**Remove:**
- `validate_test_setup.py` (subset functionality)

**Action:** Integrate test setup validation into `validate_prd_compliance.py`

#### Integration Testing
**Keep:** `test_snmp_exporter_integration.py` (specialized integration test)

#### Configuration Testing
**Keep:** `test_config.py` (focused config testing)

#### Docker Testing
**Keep:** `quick_docker_test.py` (Docker-specific testing)

#### Legacy Files
**Keep:** `setup.py` (backward compatibility, minimal file)

## Final Script Count: 13 scripts (down from 17)

### Retained Scripts:
1. `mock_snmp_agent.py` - Main entry point
2. `run_api_tests.py` - API test runner
3. `config.py` - Configuration management
4. `healthcheck.py` - Docker health check
5. `cleanup_ports.py` - Port cleanup utility
6. `performance_test.py` - Performance testing (enhanced)
7. `test_prd_requirements.py` - Basic/PRD testing (enhanced)
8. `validate_prd_compliance.py` - Validation (enhanced)
9. `test_snmp_exporter_integration.py` - Integration testing
10. `test_config.py` - Configuration testing
11. `quick_docker_test.py` - Docker testing
12. `setup.py` - Backward compatibility
13. `__init__.py` - Package marker

### Scripts to Remove:
- `quick_performance_test.py`
- `simple_prd_test.py`
- `test_basic.py`
- `validate_test_setup.py`

## Implementation Steps

### Phase 1: Enhance Retained Scripts
1. **Enhance `performance_test.py`:**
   - Add `--quick` flag for fast testing
   - Add `--simple` flag for basic PRD validation
   - Ensure all functionality from removed scripts is preserved

2. **Enhance `test_prd_requirements.py`:**
   - Integrate basic SNMP functionality tests from `test_basic.py`
   - Ensure comprehensive coverage

3. **Enhance `validate_prd_compliance.py`:**
   - Integrate test setup validation from `validate_test_setup.py`
   - Add setup validation as initial step

### Phase 2: Update Documentation
1. Update `CLAUDE.md` to reflect consolidated script usage
2. Update `Makefile` to use consolidated scripts
3. Update any shell scripts or CI/CD references

### Phase 3: Remove Redundant Scripts
1. Delete the 4 redundant scripts
2. Test all functionality to ensure nothing is broken
3. Update any remaining references

### Phase 4: Testing
1. Run full test suite to ensure no functionality lost
2. Verify all CLI options work as expected
3. Test Docker builds and operations

## Benefits After Consolidation
- Reduced maintenance burden (13 vs 17 scripts - 24% reduction)
- Clearer script purposes and responsibilities
- Eliminated functional overlap between testing scripts
- Preserved all capabilities while improving organization
- Better developer experience with fewer, more focused scripts
- Easier CI/CD maintenance with consolidated test runners

## Risk Mitigation
- Backup redundant scripts before deletion
- Thorough testing of enhanced scripts
- Gradual implementation with validation at each step
- Create compatibility shims if any external tools depend on removed scripts

## Next Steps for Implementation

### Immediate Actions Required:
1. **Audit current script usage** - ✅ COMPLETED - Found 15+ references that need updating
2. **Create backup branch** - `git checkout -b script-consolidation-backup` before making changes
3. **Test current functionality** - Run all scripts to establish baseline functionality

### Critical References Found (Must Update):
**CI/CD Workflows:**
- `.github/workflows/release.yml` - References `test_basic.py`
- `.github/workflows/ci.yml` - References `test_basic.py`

**Documentation:**
- `CLAUDE.md` - References `test_basic.py`
- `README_OLD.md` - References `test_basic.py`
- `TROUBLESHOOTING.md` - References `test_basic.py`
- `TROUBLESHOOTING_GUIDE.md` - References `quick_performance_test.py`
- `TESTING_SUMMARY.md` - References `simple_prd_test.py`
- `PRD_TESTING_STRATEGY.md` - References `simple_prd_test.py`, `quick_performance_test.py`

**Build System:**
- `Makefile` - References `test_basic.py`
- `validate_all_requirements.sh` - References `quick_performance_test.py`

### Detailed Implementation Plan:

#### Phase A: Preparation (High Priority)
1. **Create backup branch**: `git checkout -b script-consolidation-backup`
2. **Test baseline functionality**: Ensure all scripts work before changes
3. **Create replacement mapping**: Document exact command equivalents

#### Phase B: Enhancement (High Priority)
1. **Enhance test_prd_requirements.py** ⭐ (Most Critical - CI/CD dependency)
   ```bash
   # Must include ALL test_basic.py functionality
   # Add --basic flag for equivalent test_basic.py behavior
   python scripts/testing/test_prd_requirements.py --basic  # Should replace deprecated/test_basic.py
   ```

2. **Enhance performance_test.py**
   ```bash
   # Add CLI options for functionality from removed scripts
   python scripts/testing/performance_test.py --quick     # Replaces deprecated/quick_performance_test.py
   python scripts/testing/performance_test.py --simple    # Replaces deprecated/simple_prd_test.py
   ```

3. **Enhance validate_prd_compliance.py**
   ```bash
   # Add test setup validation as initial check
   python scripts/testing/validate_prd_compliance.py --setup-check  # Replaces deprecated/validate_test_setup.py
   ```

#### Phase C: Update References (Critical)
**Priority Order:**
1. **CI/CD Workflows** (Breaking changes if not updated)
   - Replace `test_basic.py` → `test_prd_requirements.py --basic`
2. **Makefile** (Build system dependency)
   - Update test-basic target
3. **Shell Scripts**
   - Update `scripts/deployment/validate_all_requirements.sh`
4. **Documentation**
   - Update all 6+ documentation files

#### Phase D: Safe Removal
```bash
# Move to deprecated directory first, test, then remove
mkdir -p deprecated
mv quick_performance_test.py deprecated/
mv simple_prd_test.py deprecated/
mv test_basic.py deprecated/
mv validate_test_setup.py deprecated/
# Test everything works, then: rm -rf deprecated/
```

## Success Criteria
- [ ] All original functionality preserved in consolidated scripts
- [ ] All tests pass with consolidated scripts
- [ ] Documentation updated to reflect new script organization
- [ ] No broken references to removed scripts
- [ ] CI/CD pipelines work with new structure
- [ ] 24% reduction in script count achieved (17 → 13 scripts)

## Estimated Timeline & Effort

| Phase | Tasks | Estimated Time | Risk Level |
|-------|-------|----------------|------------|
| **Phase A** | Preparation & baseline testing | 2-3 hours | Low |
| **Phase B** | Script enhancement with new CLI flags | 4-6 hours | Medium |
| **Phase C** | Update all references (15+ files) | 3-4 hours | High |
| **Phase D** | Safe removal & final testing | 1-2 hours | Low |
| **Total** | **Complete consolidation** | **10-15 hours** | **Medium** |

## Rollback Plan
If issues arise during implementation:
1. **Immediate**: `git checkout main` to revert all changes
2. **Partial**: Keep backup branch until full validation complete
3. **Emergency**: Restore individual scripts from `deprecated/` directory
4. **CI/CD**: Temporary compatibility shims if needed

## Ready to Execute
This plan is comprehensive and ready for implementation. The consolidation will:
- ✅ Reduce maintenance burden significantly
- ✅ Preserve all existing functionality
- ✅ Improve developer experience
- ✅ Maintain backward compatibility during transition

**Recommendation**: Execute in phases as outlined, with full testing between each phase.
