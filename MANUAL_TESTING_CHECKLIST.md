# 🧪 Manual Testing Checklist - Production Readiness

## Pre-Deployment Testing Guide

**Test Date:** `_____________`  
**Tester:** `_____________`  
**Environment:** `[ ] Localhost  [ ] Production`

---

## ✅ Core Functionality Tests

### 1. App Startup & Basic Navigation
- [ ] App starts without errors
- [ ] No KeyError messages in console/logs
- [ ] All tabs are visible and clickable
- [ ] Sidebar loads correctly
- [ ] System status indicators show correct database connections

**Expected Result:** Clean startup with no error messages

---

### 2. Study Explorer Tab (Critical)
- [ ] Tab loads without errors
- [ ] Search form appears correctly
- [ ] Can enter search criteria (organism, factor, study ID)
- [ ] "Search by Keyword" button works
- [ ] Results display correctly when found
- [ ] "Studies Found" metric appears (no duplication)
- [ ] Individual study expandable sections work
- [ ] "View Knowledge Graph" buttons appear for each study

**Test Data:**
- Organism: `mouse` or `Mus musculus`
- Factor: `spaceflight` or `microgravity`
- Study ID: `OSD-840` (if available)

**Expected Result:** Search returns relevant studies without UI duplication

---

### 3. AI Semantic Search Tab
- [ ] Tab loads without errors
- [ ] Shows appropriate message if AI search unavailable
- [ ] If available: text area for questions appears
- [ ] "Search with AI" button works
- [ ] Results display with relevance scores
- [ ] Fallback keyword search works if AI unavailable

**Test Query:** `"What are the effects of microgravity on cardiovascular system?"`

**Expected Result:** Either AI results or clear fallback message

---

### 4. Knowledge Graph Tab (Simplified)
- [ ] Tab loads without errors
- [ ] Shows appropriate message based on Neo4j availability
- [ ] If Neo4j unavailable: Clear warning message displayed
- [ ] If Neo4j available: Simple query interface appears
- [ ] Sample queries dropdown works
- [ ] "Execute Query" button functions
- [ ] Selected study information displays if coming from other tabs

**Expected Result:** Stable interface regardless of Neo4j status

---

### 5. Session State & Error Handling
- [ ] Selecting "View Knowledge Graph" from Study Explorer works
- [ ] Selected study information persists when switching tabs
- [ ] "Clear Selection" buttons work
- [ ] No KeyError messages when switching between tabs rapidly
- [ ] Browser refresh doesn't cause crashes
- [ ] "Clear Cache & Reset" button in sidebar works

**Expected Result:** Robust session management without crashes

---

### 6. Real-Time Data Tab
- [ ] Tab loads without errors
- [ ] Shows data source transparency message
- [ ] Real-time components load (ISS tracker, space weather, etc.)
- [ ] No crashes when interacting with components

**Expected Result:** Tab loads with appropriate data source indicators

---

### 7. Other Tabs (Basic Functionality)
- [ ] Research Analytics tab loads
- [ ] Ontology Browser tab loads  
- [ ] Data Sources tab loads
- [ ] Credits & Researchers tab loads
- [ ] Data & Setup tab loads

**Expected Result:** All tabs load without critical errors

---

## 🔧 Error Scenarios Testing

### 8. Database Connection Issues
- [ ] App handles MongoDB connection failures gracefully
- [ ] App handles Neo4j connection failures gracefully
- [ ] Clear error messages displayed to users
- [ ] App continues to function with available services

**Test Method:** Temporarily modify connection strings or disconnect services

---

### 9. Session State Edge Cases
- [ ] Opening multiple browser tabs works
- [ ] Rapid tab switching doesn't cause errors
- [ ] Long idle sessions don't cause KeyErrors
- [ ] Browser back/forward buttons work correctly

**Expected Result:** Stable behavior in all scenarios

---

## 📱 UI/UX Testing

### 10. Responsive Design
- [ ] App works on desktop browsers
- [ ] App works on mobile devices (if applicable)
- [ ] UI elements scale appropriately
- [ ] No overlapping or broken layouts

---

### 11. Performance
- [ ] App loads within reasonable time (< 10 seconds)
- [ ] Tab switching is responsive
- [ ] Search operations complete within reasonable time
- [ ] No memory leaks during extended use

---

## 🚨 Critical Issues Checklist

**STOP DEPLOYMENT if any of these occur:**

- [ ] ❌ KeyError messages appear in console/logs
- [ ] ❌ App crashes or becomes unresponsive
- [ ] ❌ Study Explorer search completely broken
- [ ] ❌ Database connections cause app-wide failures
- [ ] ❌ UI elements are completely missing or broken
- [ ] ❌ Session state causes persistent errors

---

## 📋 Test Results Summary

### Localhost Testing
**Date:** `_____________`
- [ ] ✅ All tests passed
- [ ] ⚠️ Minor issues found (document below)
- [ ] ❌ Critical issues found (STOP deployment)

**Issues Found:**
```
[Document any issues here]
```

### Production Testing  
**Date:** `_____________`
- [ ] ✅ All tests passed
- [ ] ⚠️ Minor issues found (document below)
- [ ] ❌ Critical issues found (STOP deployment)

**Issues Found:**
```
[Document any issues here]
```

---

## 🎯 Deployment Decision

Based on testing results:

- [ ] ✅ **APPROVED FOR PRODUCTION** - All critical tests passed
- [ ] ⚠️ **CONDITIONAL APPROVAL** - Minor issues acceptable for production
- [ ] ❌ **DEPLOYMENT BLOCKED** - Critical issues must be resolved

**Approver:** `_____________`  
**Date:** `_____________`

---

## 📞 Emergency Rollback Plan

If critical issues are discovered in production:

1. **Immediate Actions:**
   - Revert to previous stable version
   - Document the issue
   - Notify stakeholders

2. **Rollback Command:**
   ```bash
   # Use your deployment platform's rollback mechanism
   # Example: git revert or container rollback
   ```

3. **Post-Rollback:**
   - Investigate root cause
   - Fix issues in development
   - Re-run full testing cycle

---

**Testing Notes:**
- The Streamlit warnings about "missing ScriptRunContext" are expected and can be ignored
- Focus on user-facing functionality and error handling
- Test both happy path and error scenarios
- Verify the KeyError fixes are working correctly