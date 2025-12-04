"""License frontend pages."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.license import License
from app.models.license_usage import LicenseUsage
from app.models.machine_binding import MachineBinding
from app.models.magic_token import MagicToken

router = APIRouter()


@router.get("/magic", response_class=HTMLResponse)
async def magic_link_page(
    request: Request,
    token: str = Query(..., description="Magic token from email"),
    db: Session = Depends(get_db),
):
    """Magic link verification and activation page.

    Args:
        request: FastAPI request object
        token: Magic token from email
        db: Database session

    Returns:
        HTML page for magic link verification
    """
    # Verify token
    magic_token = db.query(MagicToken).filter(
        MagicToken.token == token,
        MagicToken.used_at.is_(None),
        MagicToken.expires_at > datetime.utcnow(),
    ).first()

    if not magic_token:
        # Invalid token page
        html_content = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>유효하지 않은 링크 - Convia License</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }
                .container {
                    background: white;
                    border-radius: 12px;
                    padding: 40px;
                    max-width: 500px;
                    text-align: center;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                }
                .error-icon { font-size: 64px; margin-bottom: 20px; }
                h1 { color: #f44336; margin-bottom: 10px; }
                p { color: #666; line-height: 1.6; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">❌</div>
                <h1>유효하지 않은 링크</h1>
                <p>이 매직 링크는 만료되었거나 이미 사용되었습니다.</p>
                <p style="margin-top: 20px; font-size: 0.9em; color: #999;">
                    새로운 링크가 필요하시면 라이선스 키로 다시 요청해주세요.
                </p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    # Get license information
    license_obj = db.query(License).filter(License.id == magic_token.license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    # Get usage stats
    current_usage = db.query(LicenseUsage).filter(LicenseUsage.license_id == license_obj.id).count()
    machine_bindings_count = db.query(MachineBinding).filter(MachineBinding.license_id == license_obj.id).count()

    base_url = str(request.base_url).rstrip("/")
    api_url = f"{base_url}/api"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>라이선스 활성화 - Convia License</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
            .content {{ padding: 40px; }}
            .info-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                border-left: 4px solid #667eea;
            }}
            .info-row {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #e0e0e0;
            }}
            .info-row:last-child {{ border-bottom: none; }}
            .info-label {{ font-weight: 600; color: #333; }}
            .info-value {{ color: #666; }}
            .btn {{
                display: inline-block;
                padding: 12px 30px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
                margin-top: 20px;
                transition: all 0.3s;
            }}
            .btn:hover {{
                background: #5568d3;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 라이선스 활성화</h1>
                <p>Convia 라이선스가 성공적으로 확인되었습니다</p>
            </div>
            <div class="content">
                <div class="info-card">
                    <div class="info-row">
                        <span class="info-label">라이선스 키</span>
                        <span class="info-value"><code>{license_obj.paddle_subscription_id}</code></span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">이메일</span>
                        <span class="info-value">{license_obj.email or 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">상태</span>
                        <span class="info-value">
                            <span class="status-badge status-{license_obj.status}">{license_obj.status}</span>
                        </span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">허용 컨테이너</span>
                        <span class="info-value">{license_obj.allowed_containers if license_obj.allowed_containers != -1 else '무제한'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">현재 사용</span>
                        <span class="info-value">{current_usage}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">머신 바인딩</span>
                        <span class="info-value">{machine_bindings_count}</span>
                    </div>
                </div>
                <div style="text-align: center;">
                    <a href="/license/dashboard?token={token}" class="btn">대시보드로 이동</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/dashboard", response_class=HTMLResponse)
async def license_dashboard(
    request: Request,
    token: str = Query(..., description="Magic token for authentication"),
    db: Session = Depends(get_db),
):
    """License dashboard page showing usage and bindings.

    Args:
        request: FastAPI request object
        token: Magic token for authentication
        db: Database session

    Returns:
        HTML dashboard page
    """
    # Verify token
    magic_token = db.query(MagicToken).filter(
        MagicToken.token == token,
        MagicToken.expires_at > datetime.utcnow(),
    ).first()

    if not magic_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Get license information
    license_obj = db.query(License).filter(License.id == magic_token.license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    # Get usage details
    usage_list = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_obj.id
    ).order_by(LicenseUsage.created_at.desc()).all()

    # Get machine bindings
    machine_bindings = db.query(MachineBinding).filter(
        MachineBinding.license_id == license_obj.id
    ).order_by(MachineBinding.created_at.desc()).all()

    current_usage = len(usage_list)
    allowed_containers = license_obj.allowed_containers
    usage_percentage = (current_usage / allowed_containers * 100) if allowed_containers != -1 and allowed_containers > 0 else 0

    base_url = str(request.base_url).rstrip("/")
    api_url = f"{base_url}/api"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>라이선스 대시보드 - Convia License</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
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
            }}
            .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
            .content {{ padding: 30px; }}
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
            .progress-bar {{
                width: 100%;
                height: 30px;
                background: #e0e0e0;
                border-radius: 15px;
                overflow: hidden;
                margin: 10px 0;
            }}
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, #4caf50, #8bc34a);
                transition: width 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
                font-size: 0.9em;
            }}
            .section {{
                margin-bottom: 30px;
            }}
            .section h2 {{
                margin-bottom: 15px;
                color: #333;
            }}
            .table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
            }}
            .table th {{
                background: #667eea;
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }}
            .table td {{
                padding: 15px;
                border-bottom: 1px solid #e0e0e0;
            }}
            .table tr:hover {{
                background: #f5f5f5;
            }}
            .btn-refresh {{
                padding: 10px 20px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                margin-bottom: 20px;
            }}
            .btn-refresh:hover {{
                background: #5568d3;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 라이선스 대시보드</h1>
                <p>라이선스 사용 현황 및 관리</p>
            </div>
            <div class="content">
                <div class="stats">
                    <div class="stat-card">
                        <h3>라이선스 키</h3>
                        <div class="value" style="font-size: 1.2em;"><code>{license_obj.paddle_subscription_id}</code></div>
                    </div>
                    <div class="stat-card">
                        <h3>허용 컨테이너</h3>
                        <div class="value">{allowed_containers if allowed_containers != -1 else '∞'}</div>
                    </div>
                    <div class="stat-card">
                        <h3>현재 사용</h3>
                        <div class="value">{current_usage}</div>
                    </div>
                    <div class="stat-card">
                        <h3>머신 바인딩</h3>
                        <div class="value">{len(machine_bindings)}</div>
                    </div>
                </div>

                {"<div class='progress-bar'><div class='progress-fill' style='width: " + str(min(usage_percentage, 100)) + "%;'>" + str(current_usage) + " / " + str(allowed_containers) + "</div></div>" if allowed_containers != -1 else ""}

                <div class="section">
                    <h2>컨테이너 사용 현황</h2>
                    <button class="btn-refresh" onclick="location.reload()">🔄 새로고침</button>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>머신 ID</th>
                                <th>컨테이너 ID</th>
                                <th>생성일</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f"""
                            <tr>
                                <td>{usage.id}</td>
                                <td><code>{usage.machine_id}</code></td>
                                <td><code>{usage.container_id or 'N/A'}</code></td>
                                <td>{usage.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
                            </tr>
                            """ for usage in usage_list]) if usage_list else "<tr><td colspan='4' style='text-align: center; padding: 40px; color: #999;'>사용 중인 컨테이너가 없습니다.</td></tr>"}
                        </tbody>
                    </table>
                </div>

                <div class="section">
                    <h2>머신 바인딩</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>머신 ID</th>
                                <th>바인딩일</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f"""
                            <tr>
                                <td>{binding.id}</td>
                                <td><code>{binding.machine_id}</code></td>
                                <td>{binding.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
                            </tr>
                            """ for binding in machine_bindings]) if machine_bindings else "<tr><td colspan='3' style='text-align: center; padding: 40px; color: #999;'>바인딩된 머신이 없습니다.</td></tr>"}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
