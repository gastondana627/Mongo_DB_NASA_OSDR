#!/usr/bin/env python3
"""
Test that the Streamlit app can start without errors.
"""

import sys
import subprocess
import time
import signal
import os

def test_streamlit_startup():
    """Test that Streamlit app starts without immediate errors."""
    print("🚀 Testing Streamlit app startup...")
    
    # Start Streamlit in the background
    try:
        process = subprocess.Popen(
            ["streamlit", "run", "streamlit_main_app.py", "--server.headless", "true", "--server.port", "8502"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a few seconds for startup
        print("⏳ Waiting for app to start...")
        time.sleep(5)
        
        # Check if process is still running (no immediate crash)
        if process.poll() is None:
            print("✅ App started successfully!")
            print("🌐 App should be running at http://localhost:8502")
            
            # Try to get some output
            try:
                stdout, stderr = process.communicate(timeout=2)
                if "You can now view your Streamlit app" in stdout:
                    print("✅ Streamlit server is ready!")
            except subprocess.TimeoutExpired:
                # This is expected - app is running
                pass
            
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            return True
        else:
            # Process crashed
            stdout, stderr = process.communicate()
            print("❌ App crashed during startup!")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Streamlit not found. Install with: pip install streamlit")
        return False
    except Exception as e:
        print(f"❌ Error testing startup: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 60)
    print("🧪 Streamlit App Startup Test")
    print("=" * 60)
    
    # First check our connections
    print("1. Testing database connections...")
    result = subprocess.run([sys.executable, "startup_check.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Database connections failed. Fix these first:")
        print(result.stdout)
        return 1
    
    print("✅ Database connections OK")
    
    # Test Streamlit startup
    print("\n2. Testing Streamlit app startup...")
    if test_streamlit_startup():
        print("\n🎉 All tests passed!")
        print("\n💡 To run the app manually:")
        print("   streamlit run streamlit_main_app.py")
        return 0
    else:
        print("\n❌ Streamlit startup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())