from dataclasses import dataclass


@dataclass
class Evidence:
    source: str       # e.g. "PubMed", "MedlinePlus"
    citation_id: str  # PMID, URL, or whatever identifies it within that source
    title: str
    text: str
    url: str = ""

    def as_citation(self) -> str:
        return f"[{self.source}: {self.citation_id}] {self.title}"
