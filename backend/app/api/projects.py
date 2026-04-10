from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.asset import Asset, AssetVersion
from app.models.project import Project, StepProgress
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetRead, AssetVersionRead
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, StepProgressRead

router = APIRouter(prefix='/projects', tags=['projects'])

DEFAULT_STEPS = [
    ('concept', '概念验证'),
    ('outline', '故事大纲'),
    ('characters', '角色设定'),
    ('scenes', '场景拆解'),
    ('writer-quality', '成稿润色'),
]


def _get_owned_project(db: Session, project_id: UUID, user: User) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    return project


@router.post('', response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Project:
    project = Project(
        user_id=user.id,
        title=payload.title,
        genre=payload.genre,
        description=payload.description,
        current_step_code=DEFAULT_STEPS[0][0],
    )
    db.add(project)
    db.flush()

    for index, (step_code, step_name) in enumerate(DEFAULT_STEPS):
        db.add(
            StepProgress(
                project_id=project.id,
                step_code=step_code,
                step_name=step_name,
                is_current=index == 0,
                status='in_progress' if index == 0 else 'pending',
                progress_percent=10 if index == 0 else 0,
                step_metadata={'order': index + 1},
            )
        )

    db.commit()
    db.refresh(project)
    return project


@router.get('', response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Project]:
    return list(db.scalars(select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc())).all())


@router.get('/{project_id}', response_model=ProjectRead)
def get_project(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Project:
    return _get_owned_project(db, project_id, user)


@router.put('/{project_id}', response_model=ProjectRead)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Project:
    project = _get_owned_project(db, project_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete('/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Response:
    project = _get_owned_project(db, project_id, user)
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/{project_id}/steps', response_model=list[StepProgressRead])
def get_project_steps(
    project_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[StepProgress]:
    _get_owned_project(db, project_id, user)
    return list(
        db.scalars(
            select(StepProgress)
            .where(StepProgress.project_id == project_id)
            .order_by(StepProgress.created_at.asc())
        ).all()
    )


@router.post('/{project_id}/assets', response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_or_update_asset(
    project_id: UUID,
    payload: AssetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Asset:
    _get_owned_project(db, project_id, user)

    asset = db.scalar(
        select(Asset).where(
            Asset.project_id == project_id,
            Asset.step_code == payload.step_code,
            Asset.asset_type == payload.asset_type,
        )
    )

    if asset:
        asset.version += 1
        asset.title = payload.title
        asset.content = payload.content
    else:
        asset = Asset(
            project_id=project_id,
            step_code=payload.step_code,
            asset_type=payload.asset_type,
            title=payload.title,
            content=payload.content,
            version=1,
        )
        db.add(asset)
        db.flush()

    db.add(AssetVersion(asset_id=asset.id, version=asset.version, content=payload.content))
    db.commit()
    db.refresh(asset)
    return asset


@router.get('/{project_id}/assets', response_model=list[AssetRead])
def list_assets(
    project_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Asset]:
    _get_owned_project(db, project_id, user)
    return list(db.scalars(select(Asset).where(Asset.project_id == project_id).order_by(Asset.created_at.desc())).all())


@router.get('/{project_id}/assets/{asset_id}/versions', response_model=list[AssetVersionRead])
def list_asset_versions(
    project_id: UUID,
    asset_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AssetVersion]:
    _get_owned_project(db, project_id, user)
    asset = db.scalar(select(Asset).where(Asset.id == asset_id, Asset.project_id == project_id))
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Asset not found')
    return list(
        db.scalars(
            select(AssetVersion)
            .where(AssetVersion.asset_id == asset_id)
            .order_by(AssetVersion.version.desc())
        ).all()
    )
