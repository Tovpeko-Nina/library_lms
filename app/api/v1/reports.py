from fastapi import APIRouter, Depends

from app.api.v1.deps import roles
from app.services import report as report_service


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/inventory")
def inventory(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return report_service.inventory_report()


@router.get("/inventory/missing")
def missing(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return report_service.missing_books()


@router.get("/inventory/damaged")
def damaged(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return report_service.damaged_books()


@router.get("/usage")
def usage(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return report_service.usage_report()


@router.get("/popular")
def popular():
    return report_service.popular_books()


@router.get("/borrowing-trends")
def trends(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return report_service.borrowing_trends()


@router.get("/overdue")
def overdue(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return report_service.overdue_report()


@router.get("/branch/{branch}")
def branch(branch: str, user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return report_service.branch_report(branch)
