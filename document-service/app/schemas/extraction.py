from pydantic import BaseModel


class ExtractRequest(BaseModel):
    text: str
    schema_name: str


class InvoiceData(BaseModel):
    number: str | None = None
    date: str | None = None
    amount: float | None = None
    currency: str | None = None
    counterparty: str | None = None
    description: str | None = None


class ContractData(BaseModel):
    parties: list[str] = []
    date: str | None = None
    duration: str | None = None
    subject: str | None = None
    contract_type: str | None = None


ExtractResponse = InvoiceData | ContractData
