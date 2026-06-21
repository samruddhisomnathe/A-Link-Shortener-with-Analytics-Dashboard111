import json
import sqlite3
import pandas as pd
from flask import Flask, request, redirect, render_template_string, jsonify
import database as db

# Initialize the Flask app
app = Flask(__name__)

# Initialize the SQLite database on startup
db.init_db()

# --- HTML TEMPLATES ---

# Main Dashboard Template
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Link Shield - Analytics Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #080710;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.08);
            --card-hover: rgba(255, 255, 255, 0.06);
            --primary: #E94057;
            --secondary: #8A2387;
            --tertiary: #F27121;
            --success: #10B981;
            --info: #3B82F6;
            --danger: #EF4444;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            background: radial-gradient(circle at center, #111025 0%, var(--bg-color) 100%);
            color: var(--text-primary);
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        .container {
            max-width: 1300px;
            width: 100%;
            margin: 0 auto;
            padding: 24px;
            flex-grow: 1;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--card-border);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.8rem;
            font-weight: 800;
            background: linear-gradient(90deg, var(--secondary) 0%, var(--primary) 50%, var(--tertiary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo i {
            -webkit-text-fill-color: initial;
            color: var(--primary);
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        @media (min-width: 768px) {
            .grid-2 {
                grid-template-columns: 1fr 1fr;
            }
        }

        .grid-3 {
            display: grid;
            grid-template-columns: 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        @media (min-width: 1024px) {
            .grid-3 {
                grid-template-columns: 2fr 1fr;
                gap: 24px;
            }
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            transition: all 0.3s ease;
        }

        .card:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .form-group {
            margin-bottom: 16px;
        }

        .form-group label {
            display: block;
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
            font-weight: 500;
        }

        .input-container {
            position: relative;
            display: flex;
            align-items: center;
        }

        .input-container i {
            position: absolute;
            left: 14px;
            color: var(--text-muted);
        }

        .form-input {
            width: 100%;
            padding: 12px 16px 12px 42px;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .form-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(233, 64, 87, 0.15);
        }

        .btn {
            background: linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(233, 64, 87, 0.2);
            width: 100%;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(233, 64, 87, 0.4);
            background: linear-gradient(135deg, #9C27B0 0%, #FF4081 100%);
        }

        .filter-section {
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 16px;
        }

        .filter-label {
            font-size: 1rem;
            font-weight: 500;
            color: var(--text-secondary);
        }

        .filter-select {
            padding: 10px 16px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            color: var(--text-primary);
            outline: none;
            font-family: inherit;
            cursor: pointer;
            min-width: 250px;
        }

        .filter-select:focus {
            border-color: var(--primary);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        @media (min-width: 768px) {
            .metrics-grid {
                grid-template-columns: repeat(4, 1fr);
            }
        }

        .metric-card {
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            border-left: 4px solid var(--primary);
        }

        .metric-card.m-1 { border-left-color: var(--secondary); }
        .metric-card.m-2 { border-left-color: var(--primary); }
        .metric-card.m-3 { border-left-color: var(--tertiary); }
        .metric-card.m-4 { border-left-color: var(--success); }

        .metric-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: white;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .metric-value.sub {
            font-size: 1.15rem;
            padding: 5px 0;
        }

        .table-container {
            overflow-x: auto;
            width: 100%;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            padding: 12px 16px;
            color: var(--text-secondary);
            font-weight: 500;
            border-bottom: 1px solid var(--card-border);
            font-size: 0.9rem;
        }

        td {
            padding: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            font-size: 0.95rem;
            vertical-align: middle;
        }

        tr:hover td {
            background: var(--card-hover);
        }

        .short-url-link {
            color: var(--tertiary);
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s;
        }

        .short-url-link:hover {
            color: var(--primary);
            text-decoration: underline;
        }

        .long-url-text {
            color: var(--text-secondary);
            max-width: 250px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: inline-block;
        }

        .actions {
            display: flex;
            gap: 8px;
        }

        .action-btn {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
            text-decoration: none;
        }

        .action-btn:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .action-btn.delete {
            color: var(--danger);
            border-color: rgba(239, 68, 68, 0.2);
        }

        .action-btn.delete:hover {
            background: rgba(239, 68, 68, 0.1);
        }

        .action-btn.analytics {
            color: var(--info);
            border-color: rgba(59, 130, 246, 0.2);
        }

        .action-btn.analytics:hover {
            background: rgba(59, 130, 246, 0.1);
        }

        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(8px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .modal {
            background: #0d0c1b;
            border: 1px solid var(--card-border);
            border-radius: 16px;
            max-width: 480px;
            width: 90%;
            padding: 24px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
            animation: modalFadeIn 0.3s ease-out;
            position: relative;
        }

        @keyframes modalFadeIn {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .modal-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: white;
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.2rem;
            cursor: pointer;
            transition: color 0.2s;
        }

        .modal-close:hover {
            color: white;
        }

        .modal-body {
            text-align: center;
        }

        .success-icon {
            font-size: 3rem;
            color: var(--success);
            margin-bottom: 16px;
        }

        .result-url-box {
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 20px;
            text-align: left;
        }

        .result-url-box code {
            flex-grow: 1;
            font-size: 1rem;
            color: var(--tertiary);
            word-break: break-all;
            margin-right: 12px;
        }

        .copy-icon-btn {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 1.1rem;
            transition: color 0.2s;
        }

        .copy-icon-btn:hover {
            color: white;
        }

        .qr-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-top: 15px;
            gap: 10px;
        }

        .qr-code {
            padding: 10px;
            background: white;
            border-radius: 8px;
            width: 150px;
            height: 150px;
        }

        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(16, 185, 129, 0.95);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            display: none;
            align-items: center;
            gap: 10px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            z-index: 2000;
            font-weight: 500;
        }

        .city-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .city-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 14px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 8px;
        }

        .city-name {
            font-weight: 500;
        }

        .city-country {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-left: 8px;
        }

        .city-clicks {
            font-weight: 600;
            color: var(--primary);
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-secondary);
        }

        .empty-state i {
            font-size: 3rem;
            margin-bottom: 16px;
            color: var(--text-muted);
        }

        .chart-wrapper {
            position: relative;
            height: 250px;
            width: 100%;
        }

        .chart-wrapper-large {
            position: relative;
            height: 320px;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Logo & Header -->
        <header>
            <div class="logo">
                <i class="fa-solid fa-link"></i> LINK SHIELD
            </div>
            <div>
                <span style="color: var(--text-secondary); font-size: 0.9rem;">
                    Flask & SQLite Analytics Engine
                </span>
            </div>
        </header>

        <!-- Main Dashboard Controls -->
        <div class="grid-3">
            <!-- Left Side: Shortener Panel -->
            <div class="card">
                <div class="card-title">
                    <i class="fa-solid fa-bolt" style="color: var(--tertiary);"></i> Shorten a URL
                </div>
                <form id="shortenForm" onsubmit="shortenUrl(event)">
                    <div class="form-group">
                        <label for="longUrl">Destination URL</label>
                        <div class="input-container">
                            <i class="fa-solid fa-globe"></i>
                            <input type="url" id="longUrl" class="form-input" placeholder="https://example.com/some/very/long/path" required>
                        </div>
                    </div>
                    <div class="grid-2" style="margin-bottom: 0; gap: 16px;">
                        <div class="form-group" style="margin-bottom: 0;">
                            <label for="customAlias">Custom Alias (Optional)</label>
                            <div class="input-container">
                                <i class="fa-solid fa-signature"></i>
                                <input type="text" id="customAlias" class="form-input" placeholder="promo2026">
                            </div>
                        </div>
                        <div style="display: flex; align-items: flex-end;">
                            <button type="submit" class="btn">
                                <i class="fa-solid fa-wand-magic-sparkles"></i> Shorten
                            </button>
                        </div>
                    </div>
                </form>
            </div>

            <!-- Right Side: Filter Dropdown -->
            <div class="card" style="display: flex; flex-direction: column; justify-content: center;">
                <div class="card-title" style="margin-bottom: 10px;">
                    <i class="fa-solid fa-filter" style="color: var(--info);"></i> Filter Analytics
                </div>
                <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 16px;">
                    Select a link to analyze its specific clicks and geolocations.
                </p>
                <select id="filterSelect" class="filter-select" onchange="onFilterChange()" style="width: 100%;">
                    <option value="">Overall Analytics (All Links)</option>
                    {% for item in links_list %}
                    <option value="{{ item.short_code }}" {% if filter_code == item.short_code %}selected{% endif %}>
                        /{{ item.short_code }} ({{ item.long_url[:30] }}{% if item.long_url|length > 30 %}...{% endif %})
                    </option>
                    {% endfor %}
                </select>
            </div>
        </div>

        <!-- Metrics Grid -->
        <div class="metrics-grid">
            {% if not filter_code %}
            <!-- Overall Metrics -->
            <div class="metric-card m-1">
                <div class="metric-label">Total Links</div>
                <div class="metric-value">{{ metrics.total_links }}</div>
            </div>
            <div class="metric-card m-2">
                <div class="metric-label">Total Clicks</div>
                <div class="metric-value">{{ metrics.total_clicks }}</div>
            </div>
            <div class="metric-card m-3">
                <div class="metric-label">Top Performing</div>
                <div class="metric-value sub">{{ metrics.top_link }}</div>
            </div>
            <div class="metric-card m-4">
                <div class="metric-label">Unique Countries</div>
                <div class="metric-value">{{ metrics.unique_countries }}</div>
            </div>
            {% else %}
            <!-- Single Link Metrics -->
            <div class="metric-card m-1">
                <div class="metric-label">Short Code</div>
                <div class="metric-value sub" style="color: var(--tertiary);">/{{ metrics.short_code }}</div>
            </div>
            <div class="metric-card m-2">
                <div class="metric-label">Clicks</div>
                <div class="metric-value">{{ metrics.total_clicks }}</div>
            </div>
            <div class="metric-card m-3">
                <div class="metric-label">Created Date</div>
                <div class="metric-value sub">{{ metrics.created_date }}</div>
            </div>
            <div class="metric-card m-4">
                <div class="metric-label">Unique Countries</div>
                <div class="metric-value">{{ metrics.unique_countries }}</div>
            </div>
            {% endif %}
        </div>

        <!-- Analytics Charts Grid -->
        {% if metrics.total_clicks == 0 %}
        <div class="card" style="margin-bottom: 24px;">
            <div class="empty-state">
                <i class="fa-solid fa-chart-line"></i>
                <h3>No analytics data yet</h3>
                <p style="margin-top: 8px;">Share your short links! Visitor details will appear here as soon as someone clicks.</p>
            </div>
        </div>
        {% else %}
        <div class="grid-3" style="margin-bottom: 24px;">
            <!-- Clicks trend line chart -->
            <div class="card">
                <div class="card-title">
                    <i class="fa-solid fa-chart-line" style="color: var(--primary);"></i> Click Trends Over Time
                </div>
                <div class="chart-wrapper-large">
                    <canvas id="clicksChart"></canvas>
                </div>
            </div>
            <!-- Devices doughnut chart -->
            <div class="card">
                <div class="card-title">
                    <i class="fa-solid fa-tablet-screen-button" style="color: var(--secondary);"></i> Devices Used
                </div>
                <div class="chart-wrapper-large">
                    <canvas id="deviceChart"></canvas>
                </div>
            </div>
        </div>

        <div class="grid-3">
            <!-- Top Countries Bar Chart -->
            <div class="card">
                <div class="card-title">
                    <i class="fa-solid fa-earth-americas" style="color: var(--success);"></i> Top Countries
                </div>
                <div class="chart-wrapper">
                    <canvas id="countryChart"></canvas>
                </div>
            </div>
            <!-- Top Cities List -->
            <div class="card" style="display: flex; flex-direction: column;">
                <div class="card-title">
                    <i class="fa-solid fa-city" style="color: var(--info);"></i> Top Cities
                </div>
                <div class="city-list" style="flex-grow: 1; overflow-y: auto; max-height: 250px;">
                    {% if city_list %}
                        {% for city in city_list %}
                        <div class="city-item">
                            <div>
                                <span class="city-name">{{ city.city }}</span>
                                <span class="city-country">({{ city.country }})</span>
                            </div>
                            <span class="city-clicks">{{ city.count }} clicks</span>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p style="color: var(--text-secondary); text-align: center; margin-top: 30px;">No city details logged yet.</p>
                    {% endif %}
                </div>
            </div>
        </div>

        <div class="grid-2" style="margin-top: 24px; margin-bottom: 24px;">
            <!-- OS Horizontal Bars -->
            <div class="card">
                <div class="card-title">
                    <i class="fa-solid fa-circle-nodes" style="color: var(--tertiary);"></i> Operating Systems
                </div>
                <div class="chart-wrapper" style="height: 180px;">
                    <canvas id="osChart"></canvas>
                </div>
            </div>
            <!-- Browsers Horizontal Bars -->
            <div class="card">
                <div class="card-title">
                    <i class="fa-solid fa-compass" style="color: var(--primary);"></i> Browsers Used
                </div>
                <div class="chart-wrapper" style="height: 180px;">
                    <canvas id="browserChart"></canvas>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Links Manager Panel -->
        <div class="card">
            <div class="card-title">
                <i class="fa-solid fa-list-check" style="color: var(--success);"></i> Links Manager
            </div>
            {% if not links_list %}
            <div class="empty-state">
                <i class="fa-solid fa-link-slash"></i>
                <h3>No links shortened yet</h3>
                <p style="margin-top: 8px;">Use the shortening panel above to generate your first short URL.</p>
            </div>
            {% else %}
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Short Link</th>
                            <th>Original Destination</th>
                            <th>Clicks</th>
                            <th>Created At</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in links_list %}
                        <tr>
                            <td>
                                <a href="/{{ row.short_code }}" target="_blank" class="short-url-link" id="link-{{ row.short_code }}">
                                    /{{ row.short_code }}
                                </a>
                            </td>
                            <td>
                                <span class="long-url-text" title="{{ row.long_url }}">{{ row.long_url }}</span>
                            </td>
                            <td>
                                <span class="clicks-badge" style="font-weight: 600; color: var(--text-primary);">
                                    {{ row.clicks }} clicks
                                </span>
                            </td>
                            <td style="color: var(--text-secondary); font-size: 0.85rem;">
                                {{ row.created_at }}
                            </td>
                            <td>
                                <div class="actions">
                                    <button class="action-btn" onclick="copyLink('{{ row.short_code }}')">
                                        <i class="fa-regular fa-copy"></i> Copy
                                    </button>
                                    <a href="/?filter={{ row.short_code }}" class="action-btn analytics">
                                        <i class="fa-solid fa-chart-simple"></i> Stats
                                    </a>
                                    <button class="action-btn delete" onclick="deleteLink('{{ row.short_code }}')">
                                        <i class="fa-regular fa-trash-can"></i> Delete
                                    </button>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </div>
    </div>

    <!-- Success Modal Overlay -->
    <div class="modal-overlay" id="successModal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">🎉 Link Created!</div>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <i class="fa-regular fa-circle-check success-icon"></i>
                <p style="color: var(--text-secondary); margin-bottom: 12px;">Your shortened URL is ready:</p>
                <div class="result-url-box">
                    <code id="modalShortUrl"></code>
                    <button class="copy-icon-btn" onclick="copyModalLink()" title="Copy Link">
                        <i class="fa-regular fa-copy"></i>
                    </button>
                </div>
                <div class="qr-container">
                    <span style="font-size: 0.85rem; color: var(--text-secondary);">Scan QR Code:</span>
                    <img id="modalQrCode" class="qr-code" src="" alt="QR Code">
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toastBox">
        <i class="fa-regular fa-circle-check"></i>
        <span id="toastMessage">Copied to clipboard!</span>
    </div>

    <!-- Javascript Handlers -->
    <script>
        // Copy Short URL from row
        function copyLink(shortCode) {
            const fullUrl = window.location.origin + '/' + shortCode;
            navigator.clipboard.writeText(fullUrl).then(() => {
                showToast('Short URL copied!');
            }).catch(err => {
                console.error('Failed to copy: ', err);
            });
        }

        // Copy Short URL from Modal
        function copyModalLink() {
            const codeEl = document.getElementById('modalShortUrl');
            navigator.clipboard.writeText(codeEl.textContent).then(() => {
                showToast('Short URL copied!');
            }).catch(err => {
                console.error('Failed to copy: ', err);
            });
        }

        // Show Toast Notification
        function showToast(message) {
            const toast = document.getElementById('toastBox');
            document.getElementById('toastMessage').textContent = message;
            toast.style.display = 'flex';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 2500);
        }

        // Delete Short URL
        function deleteLink(shortCode) {
            if (confirm('Are you sure you want to delete /' + shortCode + ' and all click analytics?')) {
                fetch('/api/delete/' + shortCode, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showToast('Link deleted!');
                        setTimeout(() => window.location.reload(), 800);
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(err => {
                    console.error('Delete failed:', err);
                });
            }
        }

        // Filter Dropdown Change
        function onFilterChange() {
            const val = document.getElementById('filterSelect').value;
            if (val === '') {
                window.location.href = '/';
            } else {
                window.location.href = '/?filter=' + encodeURIComponent(val);
            }
        }

        // Submit Shortening Form
        function shortenUrl(event) {
            event.preventDefault();
            const longUrl = document.getElementById('longUrl').value;
            const customAlias = document.getElementById('customAlias').value;

            fetch('/api/shorten', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ long_url: longUrl, custom_alias: customAlias })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const fullUrl = window.location.origin + '/' + data.short_code;
                    document.getElementById('modalShortUrl').textContent = fullUrl;
                    
                    // Generate QR Code dynamically
                    document.getElementById('modalQrCode').src = 'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + encodeURIComponent(fullUrl);
                    
                    // Open Modal
                    document.getElementById('successModal').style.display = 'flex';
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(err => {
                console.error('Shortening failed:', err);
                alert('An error occurred during URL shortening.');
            });
        }

        // Modal Close
        function closeModal() {
            document.getElementById('successModal').style.display = 'none';
            // Reload page to reflect new links
            window.location.reload();
        }

        // --- CHART GENERATION (Chart.js) ---
        {% if metrics.total_clicks > 0 %}
        
        // 1. Clicks Trend Chart
        const clicksTrendData = {{ clicks_trend_json | safe }};
        const clicksLabels = clicksTrendData.map(item => item.date);
        const clicksValues = clicksTrendData.map(item => item.clicks);
        const ctxClicks = document.getElementById('clicksChart').getContext('2d');
        const gradientClicks = ctxClicks.createLinearGradient(0, 0, 0, 250);
        gradientClicks.addColorStop(0, 'rgba(233, 64, 87, 0.4)');
        gradientClicks.addColorStop(1, 'rgba(233, 64, 87, 0.0)');
        
        new Chart(ctxClicks, {
            type: 'line',
            data: {
                labels: clicksLabels.length ? clicksLabels : ['No data'],
                datasets: [{
                    label: 'Clicks',
                    data: clicksValues.length ? clicksValues : [0],
                    borderColor: '#E94057',
                    borderWidth: 3,
                    backgroundColor: gradientClicks,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#F27121',
                    pointBorderColor: '#ffffff',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0d0c1b',
                        titleColor: '#ffffff',
                        bodyColor: '#e5e7eb',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#9ca3af', font: { family: 'Outfit' } }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#9ca3af', font: { family: 'Outfit' }, stepSize: 1 },
                        beginAtZero: true
                    }
                }
            }
        });

        // 2. Device Chart
        const deviceData = {{ device_json | safe }};
        const deviceLabels = deviceData.map(item => item.device);
        const deviceValues = deviceData.map(item => item.count);
        const ctxDevice = document.getElementById('deviceChart').getContext('2d');
        
        new Chart(ctxDevice, {
            type: 'doughnut',
            data: {
                labels: deviceLabels.length ? deviceLabels : ['No data'],
                datasets: [{
                    data: deviceValues.length ? deviceValues : [1],
                    backgroundColor: deviceValues.length ? ['#8A2387', '#E94057', '#F27121', '#10B981'] : ['rgba(255, 255, 255, 0.05)'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#9ca3af', font: { family: 'Outfit', size: 12 } }
                    },
                    tooltip: {
                        backgroundColor: '#0d0c1b',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                cutout: '65%'
            }
        });

        // 3. Country Chart
        const countryData = {{ country_json | safe }};
        const countryLabels = countryData.map(item => item.country);
        const countryValues = countryData.map(item => item.count);
        const ctxCountry = document.getElementById('countryChart').getContext('2d');
        
        new Chart(ctxCountry, {
            type: 'bar',
            data: {
                labels: countryLabels.length ? countryLabels : ['No data'],
                datasets: [{
                    data: countryValues.length ? countryValues : [0],
                    backgroundColor: '#10B981',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0d0c1b',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af', font: { family: 'Outfit' } }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#9ca3af', font: { family: 'Outfit' }, stepSize: 1 },
                        beginAtZero: true
                    }
                }
            }
        });

        // 4. OS Chart
        const osData = {{ os_json | safe }};
        const osLabels = osData.map(item => item.os);
        const osValues = osData.map(item => item.count);
        const ctxOS = document.getElementById('osChart').getContext('2d');
        
        new Chart(ctxOS, {
            type: 'bar',
            data: {
                labels: osLabels.length ? osLabels : ['No data'],
                datasets: [{
                    data: osValues.length ? osValues : [0],
                    backgroundColor: '#F27121',
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0d0c1b',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af', font: { family: 'Outfit' }, stepSize: 1 },
                        beginAtZero: true
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af', font: { family: 'Outfit' } }
                    }
                }
            }
        });

        // 5. Browser Chart
        const browserData = {{ browser_json | safe }};
        const browserLabels = browserData.map(item => item.browser);
        const browserValues = browserData.map(item => item.count);
        const ctxBrowser = document.getElementById('browserChart').getContext('2d');
        
        new Chart(ctxBrowser, {
            type: 'bar',
            data: {
                labels: browserLabels.length ? browserLabels : ['No data'],
                datasets: [{
                    data: browserValues.length ? browserValues : [0],
                    backgroundColor: '#8A2387',
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0d0c1b',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af', font: { family: 'Outfit' }, stepSize: 1 },
                        beginAtZero: true
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af', font: { family: 'Outfit' } }
                    }
                }
            }
        });

        {% endif %}
    </script>
</body>
</html>
"""

# Interstitial Redirect Page Template
REDIRECT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redirecting...</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        body {
            margin: 0;
            padding: 0;
            background: radial-gradient(circle at center, #1e1b4b 0%, #09090b 100%);
            color: #ffffff;
            font-family: 'Outfit', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            overflow: hidden;
        }
        .container {
            text-align: center;
            max-width: 600px;
            padding: 20px;
        }
        .spinner {
            display: inline-block;
            width: 60px;
            height: 60px;
            border: 4px rgba(255, 255, 255, 0.1) solid;
            border-top: 4px #E94057 solid;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 30px;
        }
        h2 {
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #E94057 0%, #F27121 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        p {
            color: #a0aec0;
            font-size: 1.1rem;
            margin-bottom: 30px;
        }
        .fallback {
            font-size: 0.9rem;
            color: #718096;
        }
        .fallback a {
            color: #F27121;
            text-decoration: underline;
            font-weight: 600;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner"></div>
        <h2>Taking you to your destination</h2>
        <p>Redirecting you to: <br><strong style="color: #E94057;" id="dest-label">Loading URL...</strong></p>
        <div class="fallback">
            If you are not redirected automatically in a moment, 
            <a href="#" id="fallback-link">click here</a>.
        </div>
    </div>
    
    <script>
        const shortCode = "{{ short_code }}";
        const longUrl = "{{ long_url | safe }}";
        document.getElementById('dest-label').textContent = longUrl;
        document.getElementById('fallback-link').href = longUrl;

        async function collectAndRedirect() {
            let country = "Unknown";
            let city = "Unknown";
            let device = "Desktop";
            let os = "Unknown";
            let browser = "Unknown";

            // 1. Fetch Geolocation details with a short timeout
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 1200); // 1.2s timeout
                const response = await fetch('https://ipapi.co/json/', { signal: controller.signal });
                const data = await response.json();
                if (data && !data.error) {
                    country = data.country_name || "Unknown";
                    city = data.city || "Unknown";
                }
            } catch (e) {
                console.log("Geo lookup failed or timed out", e);
            }

            // 2. Parse User-Agent for device, OS, browser
            const ua = navigator.userAgent;
            
            // OS Detection
            if (/windows/i.test(ua)) os = "Windows";
            else if (/macintosh|mac os x/i.test(ua)) os = "MacOS";
            else if (/linux/i.test(ua)) os = "Linux";
            else if (/android/i.test(ua)) os = "Android";
            else if (/iphone|ipad|ipod/i.test(ua)) os = "iOS";

            // Device Detection
            if (/mobi|android|iphone|ipad|ipod/i.test(ua)) {
                if (/ipad/i.test(ua)) device = "Tablet";
                else device = "Mobile";
            } else {
                device = "Desktop";
            }

            // Browser Detection
            if (/chrome|crios/i.test(ua) && !/edge|edg/i.test(ua) && !/opr/i.test(ua)) browser = "Chrome";
            else if (/safari/i.test(ua) && !/chrome|crios/i.test(ua)) browser = "Safari";
            else if (/firefox|fxios/i.test(ua)) browser = "Firefox";
            else if (/edge|edg/i.test(ua)) browser = "Edge";
            else if (/opr/i.test(ua)) browser = "Opera";

            // 3. Post analytics to local server
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 1000); // 1s timeout
                await fetch('/api/log_click', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        short_code: shortCode,
                        country: country,
                        city: city,
                        device: device,
                        os: os,
                        browser: browser
                    }),
                    signal: controller.signal
                });
            } catch (e) {
                console.log("Failed to log click, proceeding to redirect anyway", e);
            }

            // 4. Perform top-level redirection
            window.location.replace(longUrl);
        }

        collectAndRedirect();
    </script>
</body>
</html>
"""

# Beautiful 404 Error Template
ERROR_404_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Link Not Found</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        body {
            margin: 0;
            padding: 0;
            background: radial-gradient(circle at center, #1e1b4b 0%, #09090b 100%);
            color: #ffffff;
            font-family: 'Outfit', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            overflow: hidden;
        }
        .container {
            text-align: center;
            max-width: 500px;
            padding: 24px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        }
        h1 {
            font-size: 6rem;
            margin: 0;
            background: linear-gradient(90deg, #E94057 0%, #F27121 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }
        h2 {
            font-size: 1.8rem;
            font-weight: 600;
            margin: 10px 0 20px 0;
        }
        p {
            color: #a0aec0;
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 30px;
        }
        .btn {
            background: linear-gradient(135deg, #8A2387 0%, #E94057 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(233, 64, 87, 0.3);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(233, 64, 87, 0.5);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>404</h1>
        <h2>Link Not Found or Expired</h2>
        <p>The short link you are trying to access does not exist or has been deleted. Make sure you entered the correct URL.</p>
        <a href="/" class="btn">Go to Dashboard</a>
    </div>
</body>
</html>
"""


# --- FLASK ROUTES ---

@app.route('/')
def dashboard():
    """Main route rendering the admin analytics dashboard."""
    filter_code = request.args.get('filter')
    
    # Load all links for selection & the Link Manager list
    try:
        links_df = db.get_all_links()
    except Exception:
        links_df = pd.DataFrame(columns=['short_code', 'long_url', 'created_at', 'clicks'])
        
    links_list = links_df.to_dict(orient='records')
    
    # Fetch analytics
    try:
        analytics = db.get_analytics(filter_code)
    except Exception:
        analytics = {
            "total_clicks": 0,
            "unique_countries": 0,
            "clicks_df": pd.DataFrame(),
            "device_df": pd.DataFrame(),
            "os_df": pd.DataFrame(),
            "browser_df": pd.DataFrame(),
            "country_df": pd.DataFrame(),
            "city_df": pd.DataFrame(),
            "total_links": 0
        }
    
    # Prepare metrics block
    metrics = {
        "total_clicks": analytics.get("total_clicks", 0),
        "unique_countries": analytics.get("unique_countries", 0),
    }
    
    if not filter_code:
        metrics["total_links"] = analytics.get("total_links", 0)
        # Find top link
        if not links_df.empty and links_df['clicks'].max() > 0:
            top_link_row = links_df.sort_values(by="clicks", ascending=False).iloc[0]
            metrics["top_link"] = f"/{top_link_row['short_code']}"
            metrics["top_link_clicks"] = int(top_link_row['clicks'])
        else:
            metrics["top_link"] = "N/A"
            metrics["top_link_clicks"] = 0
    else:
        # Single link metrics
        metrics["short_code"] = filter_code
        if not links_df.empty and filter_code in links_df['short_code'].values:
            link_row = links_df[links_df['short_code'] == filter_code].iloc[0]
            metrics["created_date"] = pd.to_datetime(link_row['created_at']).strftime("%Y-%m-%d")
        else:
            metrics["created_date"] = "Unknown"
            
    # Serialize DataFrames to JSON for Chart.js
    device_json = json.dumps(analytics['device_df'].to_dict(orient='records'))
    os_json = json.dumps(analytics['os_df'].to_dict(orient='records'))
    browser_json = json.dumps(analytics['browser_df'].to_dict(orient='records'))
    country_json = json.dumps(analytics['country_df'].to_dict(orient='records'))
    
    # Clicks trend conversion
    clicks_df = analytics['clicks_df']
    clicks_trend_list = []
    if not clicks_df.empty:
        clicks_df['click_time'] = pd.to_datetime(clicks_df['click_time'])
        clicks_df['date'] = clicks_df['click_time'].dt.strftime('%Y-%m-%d')
        # Group by day
        grouped = clicks_df.groupby('date').size().reset_index(name='clicks')
        clicks_trend_list = grouped.to_dict(orient='records')
    clicks_trend_json = json.dumps(clicks_trend_list)
    
    # City list
    city_list = analytics['city_df'].to_dict(orient='records')
    
    return render_template_string(
        INDEX_HTML,
        filter_code=filter_code or '',
        links_list=links_list,
        metrics=metrics,
        device_json=device_json,
        os_json=os_json,
        browser_json=browser_json,
        country_json=country_json,
        clicks_trend_json=clicks_trend_json,
        city_list=city_list
    )


@app.route('/api/shorten', methods=['POST'])
def api_shorten():
    """Endpoint for creating a shortened link."""
    data = request.get_json()
    if not data or 'long_url' not in data:
        return jsonify({ 'success': False, 'message': 'Missing destination URL.' }), 400
    
    long_url = data['long_url']
    custom_alias = data.get('custom_alias', '').strip() or None
    
    try:
        short_code = db.shorten_url(long_url, custom_alias)
        return jsonify({ 'success': True, 'short_code': short_code })
    except ValueError as ve:
        return jsonify({ 'success': False, 'message': str(ve) }), 400
    except Exception as e:
        return jsonify({ 'success': False, 'message': f'Internal Server Error: {str(e)}' }), 500


@app.route('/api/log_click', methods=['POST'])
def api_log_click():
    """Endpoint for logging visitor click metadata."""
    data = request.get_json()
    if not data or 'short_code' not in data:
        return jsonify({ 'success': False, 'message': 'Missing short code.' }), 400
    
    short_code = data['short_code']
    country = data.get('country', 'Unknown')
    city = data.get('city', 'Unknown')
    device = data.get('device', 'Unknown')
    os = data.get('os', 'Unknown')
    browser = data.get('browser', 'Unknown')
    
    success = db.log_click(short_code, country, city, device, os, browser)
    return jsonify({ 'success': success })


@app.route('/api/delete/<short_code>', methods=['POST', 'DELETE'])
def api_delete(short_code):
    """Endpoint to delete a shortened link and its associated clicks."""
    try:
        db.delete_url(short_code)
        return jsonify({ 'success': True })
    except Exception as e:
        return jsonify({ 'success': False, 'message': str(e) }), 500


@app.route('/<short_code>')
def redirect_to_url(short_code):
    """Resolves short code redirecting to destination URL with geo/client logging page."""
    long_url = db.get_long_url(short_code)
    
    if not long_url:
        return render_template_string(ERROR_404_HTML), 404
        
    return render_template_string(
        REDIRECT_HTML,
        short_code=short_code,
        long_url=long_url
    )


if __name__ == '__main__':
    print("Starting Link Shield Web App on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
