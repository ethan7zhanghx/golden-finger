import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.models.models import Asset, AssetVersion, Project, StepProgress, User
from backend.app.schemas.project import (
    AssetCreate,
    AssetOut,
    AssetVersionOut,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    StepProgressOut,
)

STEP_CODES = [
    "writing_quality",
    "market_research",
    "worldview",
    "selling_point",
    "hook",
    "skeleton",
    "plot_beats",
    "character",
    "narrative",
    "opening",
    "dialogue",
    "pacing",
    "title",
    "script_format",
    "synopsis",
    "copyright",
]

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = Project(owner_id=user.id, **body.model_dump())
    db.add(project)
    db.flush()

    for code in STEP_CODES:
        db.add(StepProgress(project_id=project.id, step_code=code))
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(Project).filter(Project.owner_id == user.id).order_by(Project.updated_at.desc()).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(project, key, val)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()


@router.get("/{project_id}/steps", response_model=list[StepProgressOut])
def list_steps(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(StepProgress).filter(StepProgress.project_id == project_id).all()


@router.post("/{project_id}/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(
    project_id: uuid.UUID,
    body: AssetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    asset = Asset(project_id=project_id, **body.model_dump())
    db.add(asset)
    db.flush()
    db.add(AssetVersion(asset_id=asset.id, version=1, content=body.content, source="user"))
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{project_id}/assets", response_model=list[AssetOut])
def list_assets(
    project_id: uuid.UUID,
    step_code: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    q = db.query(Asset).filter(Asset.project_id == project_id)
    if step_code:
        q = q.filter(Asset.step_code == step_code)
    return q.order_by(Asset.created_at.desc()).all()


@router.get("/{project_id}/assets/{asset_id}/versions", response_model=list[AssetVersionOut])
def list_asset_versions(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return (
        db.query(AssetVersion)
        .filter(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version.desc())
        .all()
    )
