from app.core.dependencies import get_current_active_user
from app.db.fake_db import fake_items_db, next_item_id
from app.schemas.item import ItemCreate, ItemOut, ItemUpdate
from app.schemas.user import UserOut
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/api/v1/items", tags=["items"])


@router.post(
    "/",
    response_model=ItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un item (requiere JWT)",
)
async def create_item(
    item: ItemCreate, current_user: UserOut = Depends(get_current_active_user)
) -> ItemOut:
    item_id = next_item_id()
    item_out = ItemOut(id=item_id, owner=current_user.username, **item.model_dump())
    fake_items_db[item_id] = item_out
    return item_out


@router.get("/", response_model=list[ItemOut], summary="Listar mis items")
async def list_items(
    current_user: UserOut = Depends(get_current_active_user),
) -> list[ItemOut]:
    return [i for i in fake_items_db.values() if i.owner == current_user.username]


@router.get("/{item_id}", response_model=ItemOut, summary="Obtener un item por id")
async def get_item(
    item_id: int, current_user: UserOut = Depends(get_current_active_user)
) -> ItemOut:
    item = fake_items_db.get(item_id)
    if not item or item.owner != current_user.username:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return item


@router.put("/{item_id}", response_model=ItemOut, summary="Actualizar un item")
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    current_user: UserOut = Depends(get_current_active_user),
) -> ItemOut:
    item = fake_items_db.get(item_id)
    if not item or item.owner != current_user.username:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    changes = item_update.model_dump(exclude_unset=True)
    updated = item.model_copy(update=changes)
    fake_items_db[item_id] = updated
    return updated


@router.delete(
    "/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar un item"
)
async def delete_item(
    item_id: int, current_user: UserOut = Depends(get_current_active_user)
) -> None:
    item = fake_items_db.get(item_id)
    if not item or item.owner != current_user.username:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    del fake_items_db[item_id]
