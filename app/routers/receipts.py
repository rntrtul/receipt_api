from datetime import date, time
from functools import reduce
from typing import Dict, Callable, Final
from uuid import UUID, uuid4

from fastapi import APIRouter, Response, status, Request
from pydantic import BaseModel, Field, ValidationError

from .items import Item, price_str_to_cents

MIN_TIME_FOR_POINTS: Final[time] = time.fromisoformat("14:00")
MAX_TIME_FOR_POINTS: Final[time] = time.fromisoformat("16:00")

router = APIRouter(
    prefix="/receipts", tags=["receipts"], responses={404: {"description": "Not found"}}
)

receipt_points: Dict[UUID, int] = {}


class Receipt(BaseModel):
    retailer: str = Field(pattern=r"^[\w\s\-&]+$", examples=["Targee"])
    purchaseDate: date
    purchaseTime: time = Field(examples=["14:01"])
    items: list[Item] = Field(min_length=1)
    total: str = Field(pattern=r"^\d+\.\d{2}$", examples=["45.67"])

    def calculate_points(self):
        count_alpha_numerical: Callable[[int, str], int] = lambda count, char: (
            count + (1 if char.isdigit() or char.isalpha() else 0)
        )
        points = reduce(count_alpha_numerical, self.retailer, 0)

        cents = price_str_to_cents(self.total)
        points += 50 if cents % 100 == 0 else 0
        points += 25 if cents % 25 == 0 else 0

        points += 5 * (len(self.items) // 2)

        for item in self.items:
            points += item.calculate_points()

        points += 6 if self.purchaseDate.day % 2 != 0 else 0

        points += (
            10 if MIN_TIME_FOR_POINTS < self.purchaseTime < MAX_TIME_FOR_POINTS else 0
        )

        return points


@router.post("/process", status_code=status.HTTP_200_OK)
async def process_receipt(request: Request, response: Response):
    receipt_json = await request.body()
    receipt: Receipt
    try:
        receipt = Receipt.model_validate_json(receipt_json)
    except ValidationError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"description": "The receipt is invalid"}

    uid = uuid4()
    receipt_points[uid] = receipt.calculate_points()

    return {"id": uid}


@router.get("/{receipt_id}/points", status_code=status.HTTP_200_OK)
def get_receipt_points(receipt_id: str, response: Response):
    no_receipt_error = {"description": "No receipt found for that id"}

    try:
        uid: UUID = UUID(receipt_id)
    except ValueError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return no_receipt_error

    if uid in receipt_points:
        return {"points": receipt_points[uid]}

    response.status_code = status.HTTP_404_NOT_FOUND
    return no_receipt_error


class TestReceipt:
    pie = Item.model_construct(None, shortDescription="Pie", price="30.00")  # 6 points
    dew = Item.model_construct(None, shortDescription="Dew", price="6.49")  # 2 points
    sock = Item.model_construct(None, shortDescription="sock", price="3.51")  # 0 points

    april_8th = date.fromisoformat("2024-04-08")
    ten_am = time.fromisoformat("10:00")

    def test_retailer_points_alpha_num(self):
        receipt = Receipt.model_construct(
            None,
            retailer="ABC123!@# ",
            purchaseDate=self.april_8th,
            purchaseTime=self.ten_am,
            items=[],
            total="0.01",
        )

        assert receipt.calculate_points() == 6

    def test_total_points(self):
        receipt = Receipt.model_construct(
            None,
            retailer="",
            purchaseDate=self.april_8th,
            purchaseTime=self.ten_am,
            items=[],
            total="1.00",
        )

        assert receipt.calculate_points() == 75

    def test_item_count_odd(self):
        receipt = Receipt.model_construct(
            None,
            retailer="",
            purchaseDate=self.april_8th,
            purchaseTime=self.ten_am,
            items=[self.sock],
            total="0.01",
        )

        assert receipt.calculate_points() == 0

    def test_item_count_even(self):
        receipt = Receipt.model_construct(
            None,
            retailer="",
            purchaseDate=self.april_8th,
            purchaseTime=self.ten_am,
            items=[self.sock, self.sock],
            total="0.01",
        )

        assert receipt.calculate_points() == 5

    def test_items_points_added(self):
        receipt = Receipt.model_construct(
            None,
            retailer="",
            purchaseDate=self.april_8th,
            purchaseTime=self.ten_am,
            items=[self.dew, self.pie],
            total="0.01",
        )

        assert receipt.calculate_points() == (8 + 5)  # 5 for item count

    def test_purchase_day_odd(self):
        receipt = Receipt.model_construct(
            None,
            retailer="",
            purchaseDate=date.fromisoformat("2024-04-09"),
            purchaseTime=self.ten_am,
            items=[],
            total="0.01",
        )

        assert receipt.calculate_points() == 6

    def test_time_at_2pm(self):
        receipt = Receipt.model_construct(
            None,
            retailer="",
            purchaseDate=self.april_8th,
            purchaseTime=time.fromisoformat("14:00"),
            items=[],
            total="0.01",
        )

        assert receipt.calculate_points() == 0

    def test_time_after_2pm(self):
        receipt = Receipt.model_construct(
            None,
            retailer="",
            purchaseDate=self.april_8th,
            purchaseTime=time.fromisoformat("14:01"),
            items=[],
            total="0.01",
        )

        assert receipt.calculate_points() == 10

    def test_time_at_4pm(self):
        receipt = Receipt.model_construct(
            None,
            retailer="",
            purchaseDate=self.april_8th,
            purchaseTime=time.fromisoformat("16:00"),
            items=[],
            total="0.01",
        )

        assert receipt.calculate_points() == 0

    def test_full_receipt(self):
        receipt = Receipt.model_construct(
            None,
            retailer="Target",
            purchaseDate=date.fromisoformat("2024-04-09"),
            purchaseTime=time.fromisoformat("14:01"),
            items=[self.dew, self.pie],
            total="45.25",
        )

        assert receipt.calculate_points() == (6 + 25 + 5 + 8 + 6 + 10)
