"""Product repository for CRUD operations and search."""

from typing import List, Optional, Tuple

from sqlmodel import Session, select

from ..models.product import Product


class ProductRepository:
    """Repository for Product CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, product: Product) -> Product:
        """Create a new product."""
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        statement = select(Product).where(Product.id == product_id)
        return self.session.exec(statement).first()

    def get_by_product_id(self, product_id: str) -> Optional[Product]:
        """Get product by product_id field."""
        statement = select(Product).where(Product.product_id == product_id)
        return self.session.exec(statement).first()

    def list_by_tenant(self, tenant_id: int) -> List[Product]:
        """List all products for a tenant."""
        statement = (
            select(Product).where(Product.tenant_id == tenant_id).order_by(Product.name)
        )
        return list(self.session.exec(statement))

    def bulk_create(self, products: List[Product]) -> List[Product]:
        """Create multiple products in a single transaction."""
        for product in products:
            self.session.add(product)
        self.session.commit()
        for product in products:
            self.session.refresh(product)
        return products

    def search_by_tenant(
        self,
        tenant_id: int,
        query: Optional[str] = None,
        sort: str = "name",
        order: str = "asc",
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Product], int]:
        """Search products for a tenant with pagination."""
        statement = select(Product).where(Product.tenant_id == tenant_id)

        # Add search filter if query provided
        if query:
            statement = statement.where(
                Product.name.contains(query) | Product.description.contains(query)
            )

        # Add sorting
        if sort == "name":
            if order == "desc":
                statement = statement.order_by(Product.name.desc())
            else:
                statement = statement.order_by(Product.name)
        elif sort == "created_at":
            if order == "desc":
                statement = statement.order_by(Product.created_at.desc())
            else:
                statement = statement.order_by(Product.created_at)
        elif sort == "updated_at":
            if order == "desc":
                statement = statement.order_by(Product.updated_at.desc())
            else:
                statement = statement.order_by(Product.updated_at)
        elif sort == "cpm":
            if order == "desc":
                statement = statement.order_by(Product.cpm.desc())
            else:
                statement = statement.order_by(Product.cpm)
        elif sort == "delivery_type":
            if order == "desc":
                statement = statement.order_by(Product.delivery_type.desc())
            else:
                statement = statement.order_by(Product.delivery_type)

        # Get total count
        count_statement = select(Product).where(Product.tenant_id == tenant_id)
        if query:
            count_statement = count_statement.where(
                Product.name.contains(query) | Product.description.contains(query)
            )
        total = len(list(self.session.exec(count_statement)))

        # Add pagination
        statement = statement.offset((page - 1) * size).limit(size)
        products = list(self.session.exec(statement))

        return products, total

    def delete_all_by_tenant(self, tenant_id: int) -> int:
        """Delete all products for a tenant.

        Args:
            tenant_id: ID of the tenant

        Returns:
            Number of products deleted
        """
        statement = select(Product).where(Product.tenant_id == tenant_id)
        products = list(self.session.exec(statement))

        for product in products:
            self.session.delete(product)

        self.session.commit()
        return len(products)

    def update(self, product: Product) -> Product:
        """Update a product."""
        from datetime import datetime

        product.updated_at = datetime.utcnow()
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def delete(self, product_id: int) -> bool:
        """Delete a product by ID."""
        product = self.get_by_id(product_id)
        if product:
            self.session.delete(product)
            self.session.commit()
            return True
        return False
