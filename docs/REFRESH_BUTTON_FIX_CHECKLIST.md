# Refresh Button Fix - Implementation Checklist

## Problem
The refresh button is corrupting the `upstox_config.json` file by writing masked tokens instead of real tokens.

## Solution Overview
1. **Remove current refresh functionality** (corrupted implementation)
2. **Add back simple refresh function** (clean implementation)

## Phase 1: Remove Current Refresh Functionality

### Frontend Changes
- [ ] Remove "Refresh" button from UI
- [ ] Remove any frontend code that calls refresh endpoints
- [ ] Remove refresh-related state management

### Backend Changes
- [x] Remove `/api/token/refresh` endpoint from `server.py`
- [x] Remove `refresh_config()` method from `TokenValidatorModule`
- [x] Remove any other refresh-related functions

## Phase 2: Add Back Simple Refresh Function

### New Refresh Function Requirements
- [ ] Read token from `upstox_config.json`
- [ ] Test token validity by making real API call to Upstox
- [ ] Return "Valid" or "Invalid" status
- [ ] **DO NOT write anything back to config file**
- [ ] No masking, no complexity

### New Backend Implementation
- [x] Create simple refresh endpoint: `/api/token/check`
- [x] Function reads token from config file
- [x] Function tests token with Upstox API (get LTP for test stock)
- [x] Function returns simple status: `{ valid: true/false }`
- [x] Function does NOT modify any files

### New Frontend Implementation
- [ ] Add back "Check Token" button (renamed from "Refresh")
- [ ] Button calls new `/api/token/check` endpoint
- [ ] Button displays "Valid" or "Invalid" status
- [ ] Button does not modify any files

## Files to Modify

### Backend Files
- [x] `server.py` - Remove old refresh, add new check endpoint
- [x] `src/utils/token_validator_module.py` - Remove refresh_config method

### Frontend Files
- [ ] Frontend UI files - Remove refresh button, add check button
- [ ] Frontend API calls - Remove refresh calls, add check calls

## Testing
- [ ] Test that "Update and Validate" still works correctly
- [ ] Test that new "Check Token" button works without corrupting config
- [ ] Verify no files are written during token checking
- [ ] Confirm token status is accurately reported

## Success Criteria
- [ ] No more config file corruption
- [ ] Token status checking works reliably
- [ ] "Update and Validate" button continues to work
- [ ] Simple, clean implementation with no side effects