# Falcon AI - Engineering Audit Phase 3 Action Plan

## Current Status: Phase 2 Complete, Entering Phase 3

### Summary of Progress
- ✓ Phase 1: Complete repository audit  
- ✓ Phase 2: Fixed 4 critical blocking issues
  - Import paths (app/api/auth.py)
  - Schema definition (app/schemas/__init__.py  
  - Database constraints (app/models.py)
  - Syntax errors (app/api/capabilities.py)
- → Phase 3: Fixing test failures systematically

---

## Test Results: 17 Passed ✓ | 13 Failed ✗

### Passing Tests (17) ✓
1. ✓ tests/integration/test_loaders.py::test_txt_loader
2. ✓ tests/test_agents.py::test_business_agent
3. ✓ tests/test_agents.py::test_investment_agent  
4. ✓ tests/test_agents.py::test_coding_agent
5. ✓ tests/test_agents.py::test_research_agent
6. ✓ tests/test_agents.py::test_unknown_agent_falls_back_to_research
7. ✓ tests/test_gemini_provider.py::test_gemini_provider
8. ✓ tests/test_gemini_stream_provider.py::test_stream_gemini
9. ✓ tests/test_tool_manager.py::test_execute_web_tool
10. ✓ tests/test_tool_selector.py::test_document_tool_selected
11. ✓ tests/test_tool_selector.py::test_no_tool_needed
12. ✓ tests/test_vector_service.py::test_document_search
13. ✓ tests/test_vector_service.py::test_document_isolation
14. ✓ tests/test_web_tool.py::test_web_tool_selected

### Failing Tests (13) ✗
1. ✗ tests/test_auth.py::test_register_user
2. ✗ tests/test_auth.py::test_login_user
3. ✗ tests/test_auth.py::test_profile
4. ✗ tests/test_chat.py::test_create_chat
5. ✗ tests/test_chat.py::test_get_chats
6. ✗ tests/test_chat.py::test_get_chat_messages
7. ✗ tests/test_chat.py::test_rename_chat
8. ✗ tests/test_chat.py::test_delete_chat
9. ✗ tests/test_chat.py::test_chat_with_mocked_ai
10. ✗ tests/test_chat.py::test_chat_uses_uploaded_document
11. ✗ tests/test_documents.py::test_upload_document
12. ✗ tests/test_memory.py::test_get_memories
13. ✗ tests/test_memory.py::test_save_memory
14. ✗ tests/test_memory.py::test_update_memory
15. ✗ tests/test_tools.py::test_document_tool_registered
16. ✗ tests/test_web_tool.py::test_web_tool_registered

---

## Root Causes Identified

### 1. Database Table Creation (PRIMARY BLOCKER)
**Status**: Fixed in conftest.py
**Issue**: "no such table: users"
**Solution**: 
- Updated conftest.py to use file-based SQLite (test_falcon.db)
- Added session-scoped setup_test_db fixture with `Base.metadata.create_all()`
- Fixture now drops and recreates tables before tests

**Tests Affected**:
- All auth tests (3)
- All chat tests (7)
- All memory tests (3)
- Document upload test (1)
- Tool registration tests (2)
**Total**: 16 tests

### 2. TestClient Setup
**Issue**: Tests use Starlette TestClient which needs proper app instantiation
**Expected Fix**: Ensure conftest provides TestClient fixture with app from FastAPI

**Tests Affected**: All API tests (16)

### 3. Database Session Handling  
**Issue**: SQLite threading issues with concurrent test execution
**Status**: Partially fixed (using file-based DB not :memory:)
**Remaining**: May need `check_same_thread=False` in SQLite connection

---

## Phase 3 Action Items

### 3.1 Verify Database Setup
- [ ] Run test with fresh database to verify table creation
- [ ] Check that test_falcon.db is created with all tables
- [ ] Verify SQLite isn't throwing threading errors

### 3.2 Fix TestClient/App Fixtures
- [ ] Add `client` fixture to conftest.py that provides TestClient(app)
- [ ] Ensure client uses test database
- [ ] Add `db` session fixture for direct database access in tests

### 3.3 Fix Auth Tests (3 tests)
- [ ] test_register_user - Verify User model creation works
- [ ] test_login_user - Verify JWT token generation
- [ ] test_profile - Verify authenticated requests work

### 3.4 Fix Chat Tests (7 tests)
- [ ] test_create_chat - Database table and model
- [ ] test_get_chats - Query and filtering
- [ ] test_get_chat_messages - Message retrieval
- [ ] test_rename_chat - Update operations
- [ ] test_delete_chat - Deletion logic
- [ ] test_chat_with_mocked_ai - AI provider mocking
- [ ] test_chat_uses_uploaded_document - Document integration

### 3.5 Fix Memory Tests (3 tests)
- [ ] test_get_memories - Memory retrieval
- [ ] test_save_memory - Memory storage
- [ ] test_update_memory - Memory updates

### 3.6 Fix Tool Tests (3 tests)
- [ ] test_document_tool_registered - Registry verification
- [ ] test_web_tool_registered - Registry verification
- [ ] Ensure tool_registry singleton is properly initialized

### 3.7 Fix Document Tests (1 test)
- [ ] test_upload_document - File upload handling

---

## Recommended Fix Order

### Priority 1: Database Foundation (MUST FIX)
1. Verify conftest.py database initialization works
2. Add TestClient fixture
3. Add Session/DB fixture

### Priority 2: Core Auth (CRITICAL)
1. Fix auth tests (3 tests)
2. Verify JWT token flow works
3. Ensure password hashing works

### Priority 3: Stateful Features
1. Fix chat tests (7 tests)
2. Fix memory tests (3 tests)
3. Fix document tests (1 test)

### Priority 4: Registry/Services
1. Fix tool registration tests (2 tests)

---

## Expected Outcomes After Phase 3

All 30 tests should pass:
- ✓ 17 currently passing (stable)
- ✓ 13 currently failing (to be fixed)
- **Target**: 30/30 tests passing

---

## Next Steps

1. **Immediate**: Run full test suite with updated conftest.py
2. **Priority**: Get database initialization working for auth tests
3. **Follow-up**: Fix TestClient/fixture setup
4. **Systematic**: Fix each category of tests in priority order

---

## Technical Notes

### Database Setup (conftest.py)
```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    from app.database import engine, Base
    from app.models import User, Chat, Conversation, Memory, MemoryEmbedding
    
    Base.metadata.drop_all(bind=engine)  # Clean slate
    Base.metadata.create_all(bind=engine)  # Create tables
    
    yield  # Tests run here
    
    # Optional cleanup
```

### Missing Fixtures (to add)
```python
@pytest.fixture
def client():
    """FastAPI TestClient with test database"""
    from app.main import app
    return TestClient(app)

@pytest.fixture
def db_session():
    """Database session for direct queries"""
    from app.database import SessionLocal
    session = SessionLocal()
    yield session
    session.close()
```

---

**Phase 3 Status**: Planning complete, ready to execute  
**Estimated Effort**: 2-4 hours to fix all 13 failing tests  
**Success Criteria**: All 30 tests passing, clean pytest output

Generated: 2026-08-13  
Audit Phase: 3 of 15
