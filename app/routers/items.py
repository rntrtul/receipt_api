from pydantic import BaseModel, Field


def price_str_to_cents(price: str) -> int:
    parts = price.split(".")

    return (int(parts[0]) * 100) + int(parts[1])


class Item(BaseModel):
    shortDescription: str = Field(pattern=r"^[\w\s\-&]+$", examples=["Gatorade"])
    price: str = Field(pattern=r"^\d+\.\d{2}$", examples=["123.45"])

    def calculate_points(self):
        points = 0

        if len(self.shortDescription.strip()) % 3 == 0:
            adjusted_cents = int(price_str_to_cents(self.price) * 0.2)
            remainder = adjusted_cents % 100

            if remainder == 0:
                points += adjusted_cents / 100
            else:
                points += (adjusted_cents - (adjusted_cents % 100) + 100) / 100

        return points


class TestItem:
    def test_point(self):
        item = Item.model_construct(None, shortDescription="123", price="50.0")
        assert item.calculate_points() == 10

    def test_point_longer(self):
        item = Item.model_construct(None, shortDescription="123456", price="50.0")
        assert item.calculate_points() == 10

    def test_non_3_divs(self):
        item = Item.model_construct(None, shortDescription="1234", price="50.0")
        assert item.calculate_points() == 0

    def test_strip(self):
        item = Item.model_construct(None, shortDescription=" 123 ", price="50.0")
        assert item.calculate_points() == 10

    def test_white_space_inside(self):
        item = Item.model_construct(None, shortDescription="12 4", price="50.0")
        assert item.calculate_points() == 0

    def test_round_up(self):
        item = Item.model_construct(None, shortDescription="123", price="51.0")
        assert item.calculate_points() == 11  # 51 * 0.2 = 10.2

    def test_zero(self):
        item = Item.model_construct(None, shortDescription="123", price="0.0")
        assert item.calculate_points() == 0

    def test_float_cents(self):
        item = Item.model_construct(None, shortDescription="123", price="4.53")
        assert item.calculate_points() == 1

    def test_float_cents_round_down(self):
        item = Item.model_construct(None, shortDescription="123", price="4.52")
        assert item.calculate_points() == 1

    def test_min(self):
        item = Item.model_construct(None, shortDescription="a", price="0")
        assert item.calculate_points() == 0
