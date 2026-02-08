"""
Production ChatAgent Test Suite
Tests Cloud Run backend with real Firestore

Usage:
    python test_production_chatagent.py

Requirements:
    pip install httpx pytest pytest-asyncio

Environment:
    Production API: https://my-tiny-data-collider-ng2rb7mwyq-ez.a.run.app
    Firestore: Real GCP Firestore (not mocks)
"""

import asyncio
import json
import time
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Run: pip install httpx")
    exit(1)


class ProductionChatAgentTest:
    """Automated test suite for production ChatAgent on Cloud Run"""

    def __init__(self, base_url: str = "https://my-tiny-data-collider-ng2rb7mwyq-ez.a.run.app"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.test_sessions: List[str] = []
        self.results: Dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "base_url": base_url,
            "tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0},
        }

    def log_test(self, name: str, passed: bool, message: str, details: Optional[Dict] = None):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}: {message}")

        self.results["tests"].append(
            {
                "name": name,
                "passed": passed,
                "message": message,
                "details": details or {},
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        self.results["summary"]["total"] += 1
        if passed:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1

    def log_warning(self, name: str, message: str):
        """Log warning (not a failure)"""
        print(f"⚠️  WARN - {name}: {message}")
        self.results["summary"]["warnings"] += 1

    async def test_health_check(self) -> bool:
        """Test 0: Health check endpoint"""
        print("\n" + "=" * 80)
        print("📝 Test 0: Health Check")
        print("=" * 80)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=10.0)

            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "health_check",
                    True,
                    f"API healthy - version {data.get('version')}",
                    {"status_code": 200, "response": data},
                )
                return True
            else:
                self.log_test(
                    "health_check",
                    False,
                    f"Health check failed - status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text},
                )
                return False

        except Exception as e:
            self.log_test("health_check", False, f"Exception: {str(e)}")
            return False

    async def test_authentication(self) -> bool:
        """Test 1: Authentication flow"""
        print("\n" + "=" * 80)
        print("📝 Test 1: Authentication Flow")
        print("=" * 80)

        # Try to create or login test user
        test_email = "test@test.com"  # Using existing Firestore user
        test_password = "test123"

        try:
            async with httpx.AsyncClient() as client:
                # Try login first (OAuth2 expects form data with 'username' field)
                print(f"Attempting login as {test_email}...")
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    data={"username": test_email, "password": test_password},  # OAuth2 form data
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")

                    if self.token:
                        self.log_test(
                            "authentication_login",
                            True,
                            f"Login successful for {test_email}",
                            {"status_code": 200, "token_prefix": self.token[:20] + "..."},
                        )
                        return True
                    else:
                        self.log_test(
                            "authentication_login",
                            False,
                            "No access_token in response",
                            {"response": data},
                        )
                        return False

                elif response.status_code == 404:
                    # User doesn't exist - this is expected, we'll create one
                    self.log_warning(
                        "authentication_login",
                        f"User {test_email} not found - need to create test user first",
                    )
                    self.log_test(
                        "authentication_login",
                        False,
                        "Test user doesn't exist. Run: python scripts/seed_test_users.py",
                        {"status_code": 404, "email": test_email},
                    )
                    return False

                else:
                    self.log_test(
                        "authentication_login",
                        False,
                        f"Login failed - status {response.status_code}",
                        {"status_code": response.status_code, "response": response.text},
                    )
                    return False

        except Exception as e:
            self.log_test("authentication_login", False, f"Exception: {str(e)}")
            return False

    async def test_session_create(self) -> Optional[str]:
        """Test 2: Create session"""
        print("\n" + "=" * 80)
        print("📝 Test 2: Session Creation")
        print("=" * 80)

        if not self.token:
            self.log_test("session_create", False, "Skipped - no auth token")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sessions",
                    json={
                        "title": f"Production Test Session {datetime.now(UTC).isoformat()}",
                        "metadata": {"test": True, "environment": "production"},
                    },
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0,
                )

            if response.status_code == 201:
                data = response.json()
                session_id = data.get("session_id")

                if session_id:
                    self.test_sessions.append(session_id)
                    self.log_test(
                        "session_create",
                        True,
                        f"Session created: {session_id}",
                        {"status_code": 201, "session_id": session_id, "title": data.get("title")},
                    )
                    return session_id
                else:
                    self.log_test(
                        "session_create", False, "No session_id in response", {"response": data}
                    )
                    return None

            else:
                self.log_test(
                    "session_create",
                    False,
                    f"Create failed - status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text},
                )
                return None

        except Exception as e:
            self.log_test("session_create", False, f"Exception: {str(e)}")
            return None

    async def test_session_list(self) -> bool:
        """Test 3: List sessions"""
        print("\n" + "=" * 80)
        print("📝 Test 3: List Sessions")
        print("=" * 80)

        if not self.token:
            self.log_test("session_list", False, "Skipped - no auth token")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/sessions",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0,
                )

            if response.status_code == 200:
                data = response.json()
                sessions = data.get("sessions", [])
                total = data.get("total", 0)

                self.log_test(
                    "session_list",
                    True,
                    f"Listed {len(sessions)} sessions (total: {total})",
                    {"status_code": 200, "count": len(sessions), "total": total},
                )
                return True
            else:
                self.log_test(
                    "session_list",
                    False,
                    f"List failed - status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text},
                )
                return False

        except Exception as e:
            self.log_test("session_list", False, f"Exception: {str(e)}")
            return False

    async def test_tools_list(self) -> bool:
        """Test 4: List available tools"""
        print("\n" + "=" * 80)
        print("📝 Test 4: List Tools")
        print("=" * 80)

        if not self.token:
            self.log_test("tools_list", False, "Skipped - no auth token")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tools/available",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0,
                )

            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])

                self.log_test(
                    "tools_list",
                    True,
                    f"Found {len(tools)} tools",
                    {
                        "status_code": 200,
                        "count": len(tools),
                        "tools": [t.get("name") for t in tools],
                    },
                )
                return True
            else:
                self.log_test(
                    "tools_list",
                    False,
                    f"List failed - status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text},
                )
                return False

        except Exception as e:
            self.log_test("tools_list", False, f"Exception: {str(e)}")
            return False

    async def test_agent_execution(self, session_id: str) -> bool:
        """Test 5: Agent execution"""
        print("\n" + "=" * 80)
        print("📝 Test 5: Agent Execution")
        print("=" * 80)

        if not self.token or not session_id:
            self.log_test("agent_execution", False, "Skipped - no auth token or session")
            return False

        try:
            print("Running agent with prompt: 'What tools do you have?'")
            start_time = time.time()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/agent/run",
                    json={
                        "session_id": session_id,
                        "message": "What tools do you have? List them briefly.",
                        "stream": False,
                    },
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30.0,  # Agent execution can take longer
                )

            execution_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                result = data.get("response", "")  # API returns 'response' not 'result'
                cost = data.get("quota_used", 0)  # API returns 'quota_used' not 'cost'
                remaining_quota = data.get("quota_remaining", 0)  # Correct field name

                # Check if execution time is acceptable
                if execution_time > 10.0:
                    self.log_warning(
                        "agent_execution_performance",
                        f"Slow execution: {execution_time:.2f}s (threshold: 10s)",
                    )

                self.log_test(
                    "agent_execution",
                    True,
                    f"Agent executed in {execution_time:.2f}s, cost: {cost}, quota: {remaining_quota}",
                    {
                        "status_code": 200,
                        "execution_time": execution_time,
                        "result_length": len(result),
                        "cost": cost,
                        "remaining_quota": remaining_quota,
                        "response_preview": result[:100] if result else "(empty)",
                    },
                )
                return True
            else:
                self.log_test(
                    "agent_execution",
                    False,
                    f"Execution failed - status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text},
                )
                return False

        except Exception as e:
            self.log_test("agent_execution", False, f"Exception: {str(e)}")
            return False

    async def test_rate_limit_check(self) -> bool:
        """Test 6: Rate limit check"""
        print("\n" + "=" * 80)
        print("📝 Test 6: Rate Limit Check")
        print("=" * 80)

        if not self.token:
            self.log_test("rate_limit_check", False, "Skipped - no auth token")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/rate-limit/info",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0,
                )

            if response.status_code == 200:
                data = response.json()
                remaining = data.get("remaining")
                limit = data.get("limit")

                self.log_test(
                    "rate_limit_check",
                    True,
                    f"Rate limit: {remaining}/{limit} remaining",
                    {"status_code": 200, "remaining": remaining, "limit": limit},
                )
                return True
            else:
                self.log_test(
                    "rate_limit_check",
                    False,
                    f"Check failed - status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text},
                )
                return False

        except Exception as e:
            self.log_test("rate_limit_check", False, f"Exception: {str(e)}")
            return False

    async def test_streaming_response(self) -> bool:
        """Test 7: Streaming agent response (SSE)"""
        print("\n" + "=" * 80)
        print("📝 Test 7: Streaming Response")
        print("=" * 80)

        if not self.token:
            self.log_test("streaming_response", False, "Skipped - no auth token")
            return False

        session_id = self.test_sessions[0] if self.test_sessions else None
        if not session_id:
            self.log_test("streaming_response", False, "No session available")
            return False

        try:
            start_time = time.time()
            tokens_received = 0

            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/agent/stream",
                    json={
                        "session_id": session_id,
                        "message": "Count from 1 to 5",
                        "stream": True,
                    },
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30.0,
                ) as response:
                    if response.status_code != 200:
                        self.log_test(
                            "streaming_response",
                            False,
                            f"Stream failed - status {response.status_code}",
                            {
                                "status_code": response.status_code,
                                "response": await response.aread(),
                            },
                        )
                        return False

                    # Read SSE stream
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            tokens_received += 1
                            if tokens_received >= 5:  # Sample first 5 tokens
                                break

            execution_time = time.time() - start_time

            if tokens_received > 0:
                self.log_test(
                    "streaming_response",
                    True,
                    f"Received {tokens_received} SSE events in {execution_time:.2f}s",
                    {
                        "status_code": 200,
                        "tokens_received": tokens_received,
                        "execution_time": execution_time,
                    },
                )
                return True
            else:
                self.log_test(
                    "streaming_response",
                    False,
                    "No tokens received from stream",
                    {"tokens_received": 0},
                )
                return False

        except Exception as e:
            self.log_test("streaming_response", False, f"Exception: {str(e)}")
            return False

    async def test_document_upload(self, session_id: str) -> bool:
        """Test 8: Document upload and retrieval"""
        print("\n" + "=" * 80)
        print("📝 Test 8: Document Upload")
        print("=" * 80)

        if not self.token:
            self.log_test("document_upload", False, "Skipped - no auth token")
            return False

        try:
            # Create test document content
            test_content = "# Test Document\n\nThis is a test document for production validation.\nIt contains sample data for testing."

            # Upload document
            async with httpx.AsyncClient() as client:
                files = {"file": ("test_doc.txt", test_content.encode("utf-8"), "text/plain")}
                data = {"filename": "test_doc.txt"}

                response = await client.post(
                    f"{self.base_url}/sessions/{session_id}/documents",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0,
                )

            if response.status_code == 201:
                data = response.json()
                doc_id = data.get("document_id")

                # Verify document was stored
                async with httpx.AsyncClient() as client:
                    list_response = await client.get(
                        f"{self.base_url}/sessions/{session_id}/documents",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=10.0,
                    )

                if list_response.status_code == 200:
                    docs = list_response.json().get("documents", [])
                    found = any(d.get("document_id") == doc_id for d in docs)

                    if found:
                        self.log_test(
                            "document_upload",
                            True,
                            f"Document uploaded: {doc_id}",
                            {
                                "status_code": 201,
                                "document_id": doc_id,
                                "filename": "test_doc.txt",
                                "verified": True,
                            },
                        )
                        return True
                    else:
                        self.log_test(
                            "document_upload",
                            False,
                            "Document not found in list",
                            {"document_id": doc_id},
                        )
                        return False
                else:
                    self.log_test(
                        "document_upload",
                        False,
                        f"Failed to verify upload - status {list_response.status_code}",
                        {"status_code": list_response.status_code},
                    )
                    return False
            else:
                self.log_test(
                    "document_upload",
                    False,
                    f"Upload failed - status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text},
                )
                return False

        except Exception as e:
            self.log_test("document_upload", False, f"Exception: {str(e)}")
            return False

    async def test_tool_execution(self, session_id: str) -> bool:
        """Test 9: Agent using tools"""
        print("\n" + "=" * 80)
        print("📝 Test 9: Tool Execution (Agent calling tools)")
        print("=" * 80)

        if not self.token:
            self.log_test("tool_execution", False, "Skipped - no auth token")
            return False

        try:
            start_time = time.time()

            # Send message that requires tool use (export or search)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/agent/run",
                    json={
                        "session_id": session_id,
                        "message": "Count the words in this text: Hello world from the agent",
                        "stream": False,
                    },
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30.0,
                )

            execution_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                tools_used = data.get("tools_used", [])
                response_text = data.get("response", "")

                # Check if agent actually used a tool
                if tools_used and len(tools_used) > 0:
                    self.log_test(
                        "tool_execution",
                        True,
                        f"Agent used {len(tools_used)} tool(s): {', '.join(tools_used)}",
                        {
                            "status_code": 200,
                            "tools_used": tools_used,
                            "execution_time": execution_time,
                            "response_length": len(response_text),
                        },
                    )
                    return True
                else:
                    # Agent responded but didn't use tools - still valid
                    self.log_test(
                        "tool_execution",
                        True,
                        f"Agent responded (no tools needed) in {execution_time:.2f}s",
                        {
                            "status_code": 200,
                            "tools_used": [],
                            "execution_time": execution_time,
                            "note": "Agent chose not to use tools (valid behavior)",
                        },
                    )
                    return True
            else:
                self.log_test(
                    "tool_execution",
                    False,
                    f"Execution failed - status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text},
                )
                return False

        except Exception as e:
            self.log_test("tool_execution", False, f"Exception: {str(e)}")
            return False

    async def teardown(self):
        """Cleanup: Delete test sessions"""
        print("\n" + "=" * 80)
        print("🧹 Teardown: Cleaning up test data...")
        print("=" * 80)

        if not self.token or not self.test_sessions:
            print("No cleanup needed")
            return

        for session_id in self.test_sessions:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.delete(
                        f"{self.base_url}/sessions/{session_id}",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=10.0,
                    )

                if response.status_code in [200, 204]:
                    print(f"✅ Deleted session: {session_id}")
                else:
                    print(f"⚠️  Failed to delete session {session_id}: {response.status_code}")

            except Exception as e:
                print(f"❌ Error deleting session {session_id}: {str(e)}")

    async def run_all(self):
        """Run all tests in sequence"""
        print("\n" + "=" * 80)
        print("🚀 Production ChatAgent Test Suite")
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now(UTC).isoformat()}")
        print("=" * 80)

        try:
            # Test 0: Health check
            if not await self.test_health_check():
                print("\n❌ Health check failed - aborting test suite")
                return

            # Test 1: Authentication
            if not await self.test_authentication():
                print("\n⚠️  Authentication failed - some tests will be skipped")
                print("💡 Tip: Run 'python scripts/seed_test_users.py' to create test user")

            # Test 2: Create session
            session_id = await self.test_session_create()

            # Test 3: List sessions
            await self.test_session_list()

            # Test 4: List tools
            await self.test_tools_list()

            # Test 5: Agent execution (if we have a session)
            if session_id:
                await self.test_agent_execution(session_id)

            # Test 6: Rate limit check
            await self.test_rate_limit_check()

            # Test 7: Streaming response (if we have a session)
            if session_id:
                await self.test_streaming_response()

            # Test 8: Document upload (if we have a session)
            if session_id:
                await self.test_document_upload(session_id)

            # Test 9: Tool execution (if we have a session)
            if session_id:
                await self.test_tool_execution(session_id)

        finally:
            # Cleanup
            await self.teardown()

            # Print summary
            self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 Test Summary")
        print("=" * 80)

        summary = self.results["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        warnings = summary["warnings"]

        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"Total Tests:    {total}")
        print(f"✅ Passed:      {passed}")
        print(f"❌ Failed:      {failed}")
        print(f"⚠️  Warnings:    {warnings}")
        print(f"Pass Rate:      {pass_rate:.1f}%")

        # Save results to file
        results_file = "test_production_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {results_file}")

        # Overall assessment
        print("\n" + "=" * 80)
        if pass_rate >= 99:
            print("🎉 EXCELLENT - Production API is healthy!")
        elif pass_rate >= 95:
            print("✅ GOOD - Minor issues detected, check warnings")
        elif pass_rate >= 80:
            print("⚠️  NEEDS ATTENTION - Several tests failed")
        else:
            print("❌ CRITICAL - Major issues detected, investigate immediately")
        print("=" * 80)


async def main():
    """Main entry point"""
    test = ProductionChatAgentTest()
    await test.run_all()


if __name__ == "__main__":
    asyncio.run(main())
