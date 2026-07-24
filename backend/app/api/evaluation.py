"""冻结评测集与可复现实验 API。"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user, success
from app.core.models import User
from app.domain.evaluation import get_frozen_evaluation

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/summary")
def evaluation_summary(user: User = Depends(get_current_user)):
    evaluation = get_frozen_evaluation()
    return success(
        {
            "dataset": evaluation.validation,
            "rubric_version": evaluation.task_dataset["rubric_version"],
            "notes": evaluation.task_dataset["notes"],
            "can_run": user.role == "admin",
        }
    )


@router.post("/run")
def run_evaluation(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅治理管理员可以运行完整冻结评测")
    return success(get_frozen_evaluation().run(), "冻结评测运行完成")
