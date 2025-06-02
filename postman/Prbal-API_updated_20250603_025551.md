# Prbal API Documentation

This document outlines the various API endpoints available in the Prbal backend system.

## Table of Contents
- [❌ Prbal API Documentation](#prbal-api-documentation)
- [❌ Table of Contents](#table-of-contents)
- [✅ Authentication](#authentication)
  - [✅ User Registration](#user-registration)
    - [✅ Generic User Registration (Defaults to Customer Type)](#generic-user-registration-defaults-to-customer-type)
  - [✅ User Logout](#user-logout)
  - [✅ Access Token Management](#access-token-management)
    - [✅ List User's Access Tokens](#list-user's-access-tokens)
    - [✅ Revoke Specific Access Token](#revoke-specific-access-token)
    - [✅ Refresh JWT Access Token](#refresh-jwt-access-token)
- [✅ User Management](#user-management)
  - [✅ Generic User Endpoints](#generic-user-endpoints)
    - [✅ Manage Own Profile](#manage-own-profile)
    - [✅ Upload/Change Own Avatar](#uploadchange-own-avatar)
- [❌ Ensure 'avatar.jpg' exists in the directory where you run curl](#ensure-'avatar.jpg'-exists-in-the-directory-where-you-run-curl)
    - [✅ Deactivate Own Account](#deactivate-own-account)
    - [✅ Change Own Password](#change-own-password)
  - [✅ Customer Specific Endpoints](#customer-specific-endpoints)
    - [✅ Manage Own Customer Profile](#manage-own-customer-profile)
  - [❌ Provider Specific Endpoints](#provider-specific-endpoints)
    - [✅ Manage Own Provider Profile](#manage-own-provider-profile)
  - [❌ Admin Specific Endpoints (Profile)](#admin-specific-endpoints-profile)
    - [✅ Manage Own Admin Profile](#manage-own-admin-profile)
  - [❌ User Search](#user-search)
    - [✅ General User Search](#general-user-search)
    - [✅ User Search by Phone Number](#user-search-by-phone-number)
- [❌ Services & Service Requests](#services--service-requests)
  - [❌ Public Service & Category Endpoints](#public-service--category-endpoints)
  - [✅ Provider Service Management](#provider-service-management)
    - [✅ Create Service (Provider)](#create-service-provider)
    - [✅ List Own Services (Provider)](#list-own-services-provider)
    - [✅ Retrieve Own Service (Provider)](#retrieve-own-service-provider)
    - [✅ Update Own Service (Provider)](#update-own-service-provider)
    - [✅ Delete Own Service (Provider)](#delete-own-service-provider)
  - [✅ Public Service Request Endpoints](#public-service-request-endpoints)
    - [✅ Submit Public Service Request](#submit-public-service-request)
    - [✅ View Public Service Request Details](#view-public-service-request-details)
  - [✅ Service Requests (Customer)](#service-requests-customer)
    - [✅ Create Service Request (Customer)](#create-service-request-customer)
    - [✅ List Own Service Requests (Customer)](#list-own-service-requests-customer)
    - [✅ Retrieve Own Service Request (Customer)](#retrieve-own-service-request-customer)
    - [✅ Update Own Service Request (Customer)](#update-own-service-request-customer)
    - [✅ Cancel Own Service Request (Customer)](#cancel-own-service-request-customer)
  - [✅ Service Requests (Admin)](#service-requests-admin)
    - [✅ List All Service Requests (Admin)](#list-all-service-requests-admin)
    - [✅ Retrieve Service Request Details (Admin)](#retrieve-service-request-details-admin)
    - [✅ Update Service Request (Admin)](#update-service-request-admin)
- [❌ Products](#products)
  - [❌ Product Categories](#product-categories)
  - [❌ Products (Individual)](#products-individual)
- [❌ Bids](#bids)
  - [❌ Provider Bidding Actions](#provider-bidding-actions)
  - [❌ Bids - Customer View](#bids---customer-view)
  - [❌ Bids - Admin View](#bids---admin-view)
- [❌ Bookings](#bookings)
  - [❌ Create Booking](#create-booking)
  - [❌ View Booking Details](#view-booking-details)
  - [❌ Update Booking Status](#update-booking-status)
  - [❌ List Customer Bookings](#list-customer-bookings)
  - [❌ List Provider Bookings](#list-provider-bookings)
  - [❌ List Admin Bookings](#list-admin-bookings)
- [❌ Calendar Integration](#calendar-integration)
- [❌ Payment Processing](#payment-processing)
  - [❌ Create Payment Intent](#create-payment-intent)
  - [❌ Confirm Payment](#confirm-payment)
  - [❌ Retrieve Payment Details](#retrieve-payment-details)
  - [❌ List Payments (Customer/Provider/Admin)](#list-payments-customerprovideradmin)
  - [❌ Issue Refund (Admin)](#issue-refund-admin)
  - [❌ Payment Gateway Accounts (Provider)](#payment-gateway-accounts-provider)
    - [❌ Link Payment Gateway Account](#link-payment-gateway-account)
    - [❌ View Payment Gateway Account Details](#view-payment-gateway-account-details)
    - [❌ Update Payment Gateway Account](#update-payment-gateway-account)
    - [❌ Remove Payment Gateway Account](#remove-payment-gateway-account)
  - [❌ Payouts (Provider/Admin)](#payouts-provideradmin)
    - [❌ Request Payout (Provider)](#request-payout-provider)
    - [❌ View Payout History (Provider/Admin)](#view-payout-history-provideradmin)
    - [❌ Process Payouts (Admin)](#process-payouts-admin)
    - [❌ View Payout Settings (Provider/Admin)](#view-payout-settings-provideradmin)
- [❌ Messaging](#messaging)
  - [❌ Message Threads](#message-threads)
    - [❌ Create Message Thread](#create-message-thread)
    - [❌ List User Message Threads](#list-user-message-threads)
    - [❌ View Message Thread Details](#view-message-thread-details)
    - [❌ Archive Message Thread](#archive-message-thread)
    - [❌ Mark Thread as Read/Unread](#mark-thread-as-readunread)
  - [❌ Individual Messages](#individual-messages)
    - [❌ Send Message in Thread](#send-message-in-thread)
    - [❌ List Messages in Thread](#list-messages-in-thread)
    - [❌ Edit Message](#edit-message)
    - [❌ Delete Message](#delete-message)
- [❌ Notifications (HTTP)](#notifications-http)
  - [❌ List User Notifications](#list-user-notifications)
  - [❌ Mark Notification as Read](#mark-notification-as-read)
  - [❌ Mark All Notifications as Read](#mark-all-notifications-as-read)
  - [❌ Delete Notification](#delete-notification)
  - [❌ Notification Settings](#notification-settings)
    - [❌ Get Notification Settings](#get-notification-settings)
    - [❌ Update Notification Settings](#update-notification-settings)
- [❌ AI Suggestions & Feedback](#ai-suggestions--feedback)
  - [❌ AI Suggestions](#ai-suggestions)
    - [❌ Get AI Suggestions for Service Request](#get-ai-suggestions-for-service-request)
    - [❌ Get AI Suggestions for Pricing](#get-ai-suggestions-for-pricing)
    - [❌ Get AI Suggestions for Descriptions](#get-ai-suggestions-for-descriptions)
  - [❌ AI Feedback Logs](#ai-feedback-logs)
    - [❌ Submit Feedback on AI Suggestion](#submit-feedback-on-ai-suggestion)
    - [❌ List AI Feedback Logs (Admin)](#list-ai-feedback-logs-admin)
- [❌ Verifications (User Identity, etc.)](#verifications-user-identity,-etc.)
  - [❌ Submit Verification Document](#submit-verification-document)
  - [❌ Check Verification Status](#check-verification-status)
  - [❌ Admin Verification Actions](#admin-verification-actions)
    - [❌ List Pending Verifications (Admin)](#list-pending-verifications-admin)
    - [❌ Approve/Reject Verification (Admin)](#approvereject-verification-admin)
  - [❌ Submit Review for a Service/Provider](#submit-review-for-a-serviceprovider)
    - [❌ Generate Financial Report](#generate-financial-report)
  - [❌ Admin User Management](#admin-user-management)
    - [❌ List All Users (Admin)](#list-all-users-admin)
    - [❌ View User Details (Admin)](#view-user-details-admin)
    - [❌ Activate/Deactivate User (Admin)](#activatedeactivate-user-admin)
    - [❌ Assign User Roles (Admin)](#assign-user-roles-admin)
  - [❌ Admin Service Management](#admin-service-management)
    - [❌ List All Services (Admin)](#list-all-services-admin)
    - [❌ Update Service Details (Admin)](#update-service-details-admin)
    - [❌ Manage Service Categories (Admin)](#manage-service-categories-admin)
- [❌ WebSocket APIs](#websocket-apis)
  - [❌ Real-time Notifications (WebSocket)](#real-time-notifications-websocket)
  - [❌ Real-time Messaging (WebSocket)](#real-time-messaging-websocket)
  - [❌ Real-time Booking Updates (WebSocket)](#real-time-booking-updates-websocket)
- [❌ Health Checks](#health-checks)
  - [❌ System Health Endpoint](#system-health-endpoint)
  - [❌ Database Health Endpoint](#database-health-endpoint)
  - [❌ Service Dependency Health Endpoint](#service-dependency-health-endpoint)
- [❌ Metrics](#metrics)
  - [❌ Prometheus Metrics Endpoint](#prometheus-metrics-endpoint)

# ❌ Prbal API Documentation

*Documentation for this section is under development.*

## ❌ Table of Contents

*Documentation for this section is under development.*

## ✅ Authentication

*Documentation for this section is under development.*

### ✅ User Registration

*Documentation for this section is under development.*

#### ✅ Generic User Registration (Defaults to Customer Type)

*Documentation for this section is under development.*

### ✅ User Logout

*Documentation for this section is under development.*

### ✅ Access Token Management

*Documentation for this section is under development.*

#### ✅ List User's Access Tokens

*Documentation for this section is under development.*

#### ✅ Revoke Specific Access Token

*Documentation for this section is under development.*

#### ✅ Refresh JWT Access Token

*Documentation for this section is under development.*

## ✅ User Management

*Documentation for this section is under development.*

### ✅ Generic User Endpoints

*Documentation for this section is under development.*

#### ✅ Manage Own Profile

*Documentation for this section is under development.*

#### ✅ Upload/Change Own Avatar

*Documentation for this section is under development.*

# ❌ Ensure 'avatar.jpg' exists in the directory where you run curl

*Documentation for this section is under development.*

#### ✅ Deactivate Own Account

*Documentation for this section is under development.*

#### ✅ Change Own Password

*Documentation for this section is under development.*

### ✅ Customer Specific Endpoints

*Documentation for this section is under development.*

#### ✅ Manage Own Customer Profile

*Documentation for this section is under development.*

### ❌ Provider Specific Endpoints

*Documentation for this section is under development.*

#### ✅ Manage Own Provider Profile

*Documentation for this section is under development.*

### ❌ Admin Specific Endpoints (Profile)

*Documentation for this section is under development.*

#### ✅ Manage Own Admin Profile

*Documentation for this section is under development.*

### ❌ User Search

*Documentation for this section is under development.*

#### ✅ General User Search

*Documentation for this section is under development.*

#### ✅ User Search by Phone Number

*Documentation for this section is under development.*

## ❌ Services & Service Requests

*Documentation for this section is under development.*

### ❌ Public Service & Category Endpoints

*Documentation for this section is under development.*

### ✅ Provider Service Management

*Documentation for this section is under development.*

#### ✅ Create Service (Provider)

*Documentation for this section is under development.*

#### ✅ List Own Services (Provider)

*Documentation for this section is under development.*

#### ✅ Retrieve Own Service (Provider)

*Documentation for this section is under development.*

#### ✅ Update Own Service (Provider)

*Documentation for this section is under development.*

#### ✅ Delete Own Service (Provider)

*Documentation for this section is under development.*

### ✅ Public Service Request Endpoints

*Documentation for this section is under development.*

#### ✅ Submit Public Service Request

*Documentation for this section is under development.*

#### ✅ View Public Service Request Details

*Documentation for this section is under development.*

### ✅ Service Requests (Customer)

*Documentation for this section is under development.*

#### ✅ Create Service Request (Customer)

*Documentation for this section is under development.*

#### ✅ List Own Service Requests (Customer)

*Documentation for this section is under development.*

#### ✅ Retrieve Own Service Request (Customer)

*Documentation for this section is under development.*

#### ✅ Update Own Service Request (Customer)

*Documentation for this section is under development.*

#### ✅ Cancel Own Service Request (Customer)

*Documentation for this section is under development.*

### ✅ Service Requests (Admin)

*Documentation for this section is under development.*

#### ✅ List All Service Requests (Admin)

*Documentation for this section is under development.*

#### ✅ Retrieve Service Request Details (Admin)

*Documentation for this section is under development.*

#### ✅ Update Service Request (Admin)

*Documentation for this section is under development.*

## ❌ Products

*Documentation for this section is under development.*

### ❌ Product Categories

*Documentation for this section is under development.*

### ❌ Products (Individual)

*Documentation for this section is under development.*

## ❌ Bids

*Documentation for this section is under development.*

### ❌ Provider Bidding Actions

*Documentation for this section is under development.*

### ❌ Bids - Customer View

*Documentation for this section is under development.*

### ❌ Bids - Admin View

*Documentation for this section is under development.*

## ❌ Bookings

*Documentation for this section is under development.*

### ❌ Create Booking

*Documentation for this section is under development.*

### ❌ View Booking Details

*Documentation for this section is under development.*

### ❌ Update Booking Status

*Documentation for this section is under development.*

### ❌ List Customer Bookings

*Documentation for this section is under development.*

### ❌ List Provider Bookings

*Documentation for this section is under development.*

### ❌ List Admin Bookings

*Documentation for this section is under development.*

## ❌ Calendar Integration

*Documentation for this section is under development.*

## ❌ Payment Processing

*Documentation for this section is under development.*

### ❌ Create Payment Intent

*Documentation for this section is under development.*

### ❌ Confirm Payment

*Documentation for this section is under development.*

### ❌ Retrieve Payment Details

*Documentation for this section is under development.*

### ❌ List Payments (Customer/Provider/Admin)

*Documentation for this section is under development.*

### ❌ Issue Refund (Admin)

*Documentation for this section is under development.*

### ❌ Payment Gateway Accounts (Provider)

*Documentation for this section is under development.*

#### ❌ Link Payment Gateway Account

*Documentation for this section is under development.*

#### ❌ View Payment Gateway Account Details

*Documentation for this section is under development.*

#### ❌ Update Payment Gateway Account

*Documentation for this section is under development.*

#### ❌ Remove Payment Gateway Account

*Documentation for this section is under development.*

### ❌ Payouts (Provider/Admin)

*Documentation for this section is under development.*

#### ❌ Request Payout (Provider)

*Documentation for this section is under development.*

#### ❌ View Payout History (Provider/Admin)

*Documentation for this section is under development.*

#### ❌ Process Payouts (Admin)

*Documentation for this section is under development.*

#### ❌ View Payout Settings (Provider/Admin)

*Documentation for this section is under development.*

## ❌ Messaging

*Documentation for this section is under development.*

### ❌ Message Threads

*Documentation for this section is under development.*

#### ❌ Create Message Thread

*Documentation for this section is under development.*

#### ❌ List User Message Threads

*Documentation for this section is under development.*

#### ❌ View Message Thread Details

*Documentation for this section is under development.*

#### ❌ Archive Message Thread

*Documentation for this section is under development.*

#### ❌ Mark Thread as Read/Unread

*Documentation for this section is under development.*

### ❌ Individual Messages

*Documentation for this section is under development.*

#### ❌ Send Message in Thread

*Documentation for this section is under development.*

#### ❌ List Messages in Thread

*Documentation for this section is under development.*

#### ❌ Edit Message

*Documentation for this section is under development.*

#### ❌ Delete Message

*Documentation for this section is under development.*

## ❌ Notifications (HTTP)

*Documentation for this section is under development.*

### ❌ List User Notifications

*Documentation for this section is under development.*

### ❌ Mark Notification as Read

*Documentation for this section is under development.*

### ❌ Mark All Notifications as Read

*Documentation for this section is under development.*

### ❌ Delete Notification

*Documentation for this section is under development.*

### ❌ Notification Settings

*Documentation for this section is under development.*

#### ❌ Get Notification Settings

*Documentation for this section is under development.*

#### ❌ Update Notification Settings

*Documentation for this section is under development.*

## ❌ AI Suggestions & Feedback

*Documentation for this section is under development.*

### ❌ AI Suggestions

*Documentation for this section is under development.*

#### ❌ Get AI Suggestions for Service Request

*Documentation for this section is under development.*

#### ❌ Get AI Suggestions for Pricing

*Documentation for this section is under development.*

#### ❌ Get AI Suggestions for Descriptions

*Documentation for this section is under development.*

### ❌ AI Feedback Logs

*Documentation for this section is under development.*

#### ❌ Submit Feedback on AI Suggestion

*Documentation for this section is under development.*

#### ❌ List AI Feedback Logs (Admin)

*Documentation for this section is under development.*

## ❌ Verifications (User Identity, etc.)

*Documentation for this section is under development.*

### ❌ Submit Verification Document

*Documentation for this section is under development.*

### ❌ Check Verification Status

*Documentation for this section is under development.*

### ❌ Admin Verification Actions

*Documentation for this section is under development.*

#### ❌ List Pending Verifications (Admin)

*Documentation for this section is under development.*

#### ❌ Approve/Reject Verification (Admin)

*Documentation for this section is under development.*

### ❌ Submit Review for a Service/Provider

*Documentation for this section is under development.*

#### ❌ Generate Financial Report

*Documentation for this section is under development.*

### ❌ Admin User Management

*Documentation for this section is under development.*

#### ❌ List All Users (Admin)

*Documentation for this section is under development.*

#### ❌ View User Details (Admin)

*Documentation for this section is under development.*

#### ❌ Activate/Deactivate User (Admin)

*Documentation for this section is under development.*

#### ❌ Assign User Roles (Admin)

*Documentation for this section is under development.*

### ❌ Admin Service Management

*Documentation for this section is under development.*

#### ❌ List All Services (Admin)

*Documentation for this section is under development.*

#### ❌ Update Service Details (Admin)

*Documentation for this section is under development.*

#### ❌ Manage Service Categories (Admin)

*Documentation for this section is under development.*

## ❌ WebSocket APIs

*Documentation for this section is under development.*

### ❌ Real-time Notifications (WebSocket)

*Documentation for this section is under development.*

### ❌ Real-time Messaging (WebSocket)

*Documentation for this section is under development.*

### ❌ Real-time Booking Updates (WebSocket)

*Documentation for this section is under development.*

## ❌ Health Checks

*Documentation for this section is under development.*

### ❌ System Health Endpoint

*Documentation for this section is under development.*

### ❌ Database Health Endpoint

*Documentation for this section is under development.*

### ❌ Service Dependency Health Endpoint

*Documentation for this section is under development.*

## ❌ Metrics

*Documentation for this section is under development.*

### ❌ Prometheus Metrics Endpoint

*Documentation for this section is under development.*
