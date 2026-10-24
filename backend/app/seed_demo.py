from uuid import uuid4

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Factory, FactoryOrderNumber, ProcurementRequest, RequestFactory
from app.models.factory import DispatchMethod, FactoryStatus


def seed_demo_data() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(Factory).count() > 0:
            return

        factories = [
            Factory(
                id=str(uuid4()),
                name="Краснодарский завод кровельных материалов",
                short_name="КЗКМ",
                contact_person="Иван Петров",
                phone="+7 (861) 111-22-33",
                whatsapp="+7 (901) 111-22-33",
                email="sales@kzkm.ru",
                website="https://kzkm.ru",
                address="Краснодар, ул. Лесная, 14",
                products="Металлочерепица, профлист, доборные элементы",
                default_dispatch_method=DispatchMethod.WHATSAPP,
                payment_terms="Предоплата 30%, остальное по факту",
                production_lead_time_days=12,
                status=FactoryStatus.ACTIVE,
            ),
            Factory(
                id=str(uuid4()),
                name="Екатеринбургский завод металлопроката",
                short_name="ЕЗМ",
                contact_person="Ольга Смирнова",
                phone="+7 (343) 333-44-55",
                whatsapp="+7 (912) 333-44-55",
                email="sales@ezm.ru",
                website="https://ezm.ru",
                address="Екатеринбург, ул. Заводская, 5",
                products="Профнастил, водостоки, комплектующие",
                default_dispatch_method=DispatchMethod.EMAIL,
                payment_terms="30% аванс, 70% при отгрузке",
                production_lead_time_days=18,
                status=FactoryStatus.ACTIVE,
            ),
        ]
        db.add_all(factories)
        db.commit()

        request = ProcurementRequest(
            id=str(uuid4()),
            bitrix_deal_id="1542",
            bitrix_category_id="crm_deal_category",
            bitrix_stage_id="new",
            bitrix_title="Склад в Новороссийске",
            bitrix_url="https://example.bitrix24.ru/crm/deal/details/1542/",
            bitrix_responsible_id="42",
            bitrix_created_at=None,
            last_synced_at=None,
            owner_id="admin",
        )
        db.add(request)
        db.commit()

        rf1 = RequestFactory(
            id=str(uuid4()),
            procurement_request_id=request.id,
            factory_id=factories[0].id,
            dispatch_datetime=None,
            dispatch_method=DispatchMethod.WHATSAPP.value,
            created_by="admin",
            updated_by="admin",
        )
        rf2 = RequestFactory(
            id=str(uuid4()),
            procurement_request_id=request.id,
            factory_id=factories[1].id,
            dispatch_datetime=None,
            dispatch_method=DispatchMethod.EMAIL.value,
            created_by="admin",
            updated_by="admin",
        )
        db.add_all([rf1, rf2])
        db.commit()

        db.add_all([
            FactoryOrderNumber(id=str(uuid4()), request_factory_id=rf1.id, order_number="З-1025"),
            FactoryOrderNumber(id=str(uuid4()), request_factory_id=rf1.id, order_number="З-1028"),
            FactoryOrderNumber(id=str(uuid4()), request_factory_id=rf2.id, order_number="З-205"),
        ])
        db.commit()
    finally:
        db.close()
