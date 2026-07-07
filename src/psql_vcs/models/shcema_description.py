from dataclasses import dataclass, field


@dataclass
class ForeignKeyInfo:
    columns: list[str] = field(default_factory=list)
    ref_table: str | None = None
    ref_columns: list[str] = field(default_factory=list)
    del_upd: str | None = None
