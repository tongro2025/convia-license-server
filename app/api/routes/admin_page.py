"""Admin management page routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.security import verify_admin_api_key
from app.db.session import get_db
from app.models.license import License
from app.models.license_usage import LicenseUsage
from app.models.machine_binding import MachineBinding

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    x_admin_api_key: Optional[str] = Header(None, alias="X-Admin-API-Key"),
    admin_key: Optional[str] = Query(None, alias="admin_key"),
    db: Session = Depends(get_db),
):
    """Admin management page for license and container management."""

    # 1) Determine API key: header > query param
    api_key = x_admin_api_key or admin_key
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail=(
                "Admin API key is required. "
                "Send 'X-Admin-API-Key' header or 'admin_key' query parameter."
            ),
        )

    # 2) Validate key
    verify_admin_api_key(api_key)

    # 3) Load licenses and usage info
    licenses = db.query(License).all()
    licenses_data = []
    for license_obj in licenses:
        current_usage = (
            db.query(LicenseUsage)
            .filter(LicenseUsage.license_id == license_obj.id)
            .count()
        )
        machine_bindings_count = (
            db.query(MachineBinding)
            .filter(MachineBinding.license_id == license_obj.id)
            .count()
        )
        licenses_data.append(
            {
                "id": license_obj.id,
                "license_key": license_obj.paddle_subscription_id,
                "email": license_obj.email or "N/A",
                "status": license_obj.status,
                "allowed_containers": (
                    license_obj.allowed_containers
                    if license_obj.allowed_containers != -1
                    else "무제한"
                ),
                "current_usage": current_usage,
                "machine_bindings_count": machine_bindings_count,
                "created_at": license_obj.created_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if license_obj.created_at
                else "N/A",
            }
        )

    # 3-1) Pre-render table rows HTML (복잡한 f-string 피하기)
    rows_parts = []
    for l in licenses_data:
        if isinstance(l["allowed_containers"], int):
            if l["current_usage"] < l["allowed_containers"]:
                usage_class = "usage-ok"
            elif l["current_usage"] == l["allowed_containers"]:
                usage_class = "usage-warning"
            else:
                usage_class = "usage-full"
        else:  # "무제한"
            usage_class = "usage-ok"

        row_html = f"""
                        <tr data-license-id="{l['id']}">
                            <td>{l['id']}</td>
                            <td><code>{l['license_key']}</code></td>
                            <td>{l['email']}</td>
                            <td><span class="status-badge status-{l['status']}">{l['status']}</span></td>
                            <td>{l['allowed_containers']}</td>
                            <td>
                                <span class="usage-indicator {usage_class}">
                                    {l['current_usage']}
                                </span>
                            </td>
                            <td>{l['machine_bindings_count']}</td>
                            <td>{l['created_at']}</td>
                            <td class="actions">
                                <button class="btn btn-reset-containers" onclick="resetContainers({l['id']})">
                                    컨테이너 리셋
                                </button>
                                <button class="btn btn-reset" onclick="resetMachines({l['id']})">
                                    머신 리셋
                                </button>
                            </td>
                        </tr>
        """
        rows_parts.append(row_html)

    rows_html = "\n".join(rows_parts)

    # 4) API base URL (for reset endpoints)
    base_url = str(request.base_url).rstrip("/")
    api_url = f"{base_url}/api/admin/licenses"

    # 5) Build HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Convia License 관리 페이지</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            .header p {{
                opacity: 0.9;
                font-size: 1.1em;
            }}
            .content {{
                padding: 30px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}
            .stat-card h3 {{
                color: #667eea;
                font-size: 0.9em;
                text-transform: uppercase;
                margin-bottom: 10px;
            }}
            .stat-card .value {{
                font-size: 2em;
                font-weight: bold;
                color: #333;
            }}
            .license-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: white;
            }}
            .license-table th {{
                background: #667eea;
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }}
            .license-table td {{
                padding: 15px;
                border-bottom: 1px solid #e0e0e0;
            }}
            .license-table tr:hover {{
                background: #f5f5f5;
            }}
            .status-badge {{
                display: inline-block;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
            }}
            .status-active {{
                background: #4caf50;
                color: white;
            }}
            .status-cancelled {{
                background: #f44336;
                color: white;
            }}
            .status-expired {{
                background: #ff9800;
                color: white;
            }}
            .usage-indicator {{
                display: inline-block;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
            }}
            .usage-ok {{
                background: #4caf50;
                color: white;
            }}
            .usage-warning {{
                background: #ff9800;
                color: white;
            }}
            .usage-full {{
                background: #f44336;
                color: white;
            }}
            .btn {{
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.9em;
                font-weight: 600;
                transition: all 0.3s;
                margin: 2px;
            }}
            .btn-reset {{
                background: #ff9800;
                color: white;
            }}
            .btn-reset:hover {{
                background: #f57c00;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }}
            .btn-reset-containers {{
                background: #2196f3;
                color: white;
            }}
            .btn-reset-containers:hover {{
                background: #1976d2;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }}
            .btn:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            .actions {{
                display: flex;
                gap: 5px;
            }}
            .loading {{
                display: none;
                text-align: center;
                padding: 20px;
                color: #667eea;
            }}
            .message {{
                padding: 15px;
                margin: 10px 0;
                border-radius: 6px;
                display: none;
            }}
            .message-success {{
                background: #4caf50;
                color: white;
            }}
            .message-error {{
                background: #f44336;
                color: white;
            }}
            .search-box {{
                margin-bottom: 20px;
            }}
            .search-box input {{
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 1em;
            }}
            .search-box input:focus {{
                outline: none;
                border-color: #667eea;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Convia License 관리</h1>
                <p>라이선스 및 컨테이너 관리 대시보드</p>
            </div>
            <div class="content">
                <div class="stats">
                    <div class="stat-card">
                        <h3>전체 라이선스</h3>
                        <div class="value" id="total-licenses">{len(licenses_data)}</div>
                    </div>
                    <div class="stat-card">
                        <h3>활성 라이선스</h3>
                        <div class="value" id="active-licenses">{sum(1 for l in licenses_data if l['status'] == 'active')}</div>
                    </div>
                    <div class="stat-card">
                        <h3>전체 컨테이너 사용</h3>
                        <div class="value" id="total-containers">{sum(l['current_usage'] for l in licenses_data)}</div>
                    </div>
                </div>

                <div class="message" id="message"></div>

                <div class="search-box">
                    <input type="text" id="search-input" placeholder="라이선스 키, 이메일, 상태로 검색...">
                </div>

                <table class="license-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>라이선스 키</th>
                            <th>이메일</th>
                            <th>상태</th>
                            <th>허용 컨테이너</th>
                            <th>현재 사용</th>
                            <th>머신 바인딩</th>
                            <th>생성일</th>
                            <th>작업</th>
                        </tr>
                    </thead>
                    <tbody id="license-tbody">
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            const API_URL = '{api_url}';
            const ADMIN_API_KEY = '{api_key}';

            function showMessage(text, type = 'success') {{
                const messageEl = document.getElementById('message');
                messageEl.textContent = text;
                messageEl.className = `message message-${{type}}`;
                messageEl.style.display = 'block';
                setTimeout(() => {{
                    messageEl.style.display = 'none';
                }}, 5000);
            }}

            async function resetContainers(licenseId) {{
                if (!confirm(`라이선스 #${{licenseId}}의 컨테이너 사용량을 리셋하시겠습니까?`)) {{
                    return;
                }}

                try {{
                    const response = await fetch(`${{API_URL}}/${{licenseId}}/reset-containers`, {{
                        method: 'POST',
                        headers: {{
                            'X-Admin-API-Key': ADMIN_API_KEY,
                            'Content-Type': 'application/json',
                        }},
                    }});

                    const data = await response.json();
                    if (response.ok) {{
                        showMessage('컨테이너 사용량이 리셋되었습니다.', 'success');
                        setTimeout(() => location.reload(), 1000);
                    }} else {{
                        showMessage(data.detail || '리셋 실패', 'error');
                    }}
                }} catch (error) {{
                    showMessage('오류가 발생했습니다: ' + error.message, 'error');
                }}
            }}

            async function resetMachines(licenseId) {{
                if (!confirm(`라이선스 #${{licenseId}}의 머신 바인딩을 리셋하시겠습니까?`)) {{
                    return;
                }}

                try {{
                    const response = await fetch(`${{API_URL}}/${{licenseId}}/reset-machines`, {{
                        method: 'POST',
                        headers: {{
                            'X-Admin-API-Key': ADMIN_API_KEY,
                            'Content-Type': 'application/json',
                        }},
                    }});

                    const data = await response.json();
                    if (response.ok) {{
                        showMessage('머신 바인딩이 리셋되었습니다.', 'success');
                        setTimeout(() => location.reload(), 1000);
                    }} else {{
                        showMessage(data.detail || '리셋 실패', 'error');
                    }}
                }} catch (error) {{
                    showMessage('오류가 발생했습니다: ' + error.message, 'error');
                }}
            }}

            // Search functionality
            document.getElementById('search-input').addEventListener('input', function(e) {{
                const searchTerm = e.target.value.toLowerCase();
                const rows = document.querySelectorAll('#license-tbody tr');
                
                rows.forEach(row => {{
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                }});
            }});
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)