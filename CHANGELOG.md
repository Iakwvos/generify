# Changelog

All notable changes to this project will be documented in this file.

## [Initial Analysis] - 2024-03-21

### Added
- Comprehensive documentation of all available endpoints
- Analysis of API key usage in configuration
- Documentation of authentication system
- Documentation of main application structure

### API Keys Documented
- Shopify API Key (ACCESS_TOKEN) for store operations
- Gemini API Key for AI features
- Supabase API Key for authentication and database

### Endpoints Documented
- Authentication endpoints (/auth/*)
- Main page routes (/)
- API endpoints (/api/*)
  - Products management
  - AI features
  - Image processing
  - Template management
  - Store configuration
  - Theme management

### Security Features
- Login required decorator for protected routes
- API key authentication for API endpoints
- Session management for user authentication
- Secure password reset flow

## [Unreleased]

### Fixed
- Fixed product creation endpoint using wrong method (duplicate_product instead of create_product)
- Added proper error handling for product creation failures
- Added detailed logging throughout product creation process
- Added validation for required fields in product creation
- Fixed product creation endpoint to properly handle new product requests
- Added proper error handling for product creation
- Added validation for required fields in product creation
- Corrected image extraction endpoint URL from '/api/ai/extract-images' to '/api/images/extract-images'
- Added missing sidebar CSS file with responsive design
- Fixed session reference error in ProductActions.js
- Improved API key retrieval with better error handling
- Added missing API key authentication in dashboard UI for image extraction
- Updated ProductActions.js to properly include X-API-KEY header from session storage

### Added
- Detailed logging for product creation process
- Step-by-step tracking of image processing
- Better error messages for API responses
- New product creation validation
- Better error messages for product creation
- Reference URL tracking in product metafields
- New sidebar component styles with mobile responsiveness
- API key initialization check in ProductActions
- Graceful degradation for missing API keys
- API key retrieval method in ProductActions class
- Multiple fallback options for API key storage (localStorage, sessionStorage)

### Security
- Improved API authentication consistency across all endpoints
- Standardized API key header usage in frontend requests
- Added warning for missing API keys
- Enhanced error handling for storage access
