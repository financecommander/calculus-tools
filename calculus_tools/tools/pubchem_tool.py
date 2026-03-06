"""PubChem Chemistry Tool — Compound search, properties, structures.

Free, no API key. Rate-limited (5 req/sec recommended).
Docs: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import requests


_PUG_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


class PubChemInput(BaseModel):
    query: str = Field(
        ..., description="Compound name, CID, SMILES, or InChI (e.g. 'aspirin', '2244')"
    )
    search_type: str = Field(
        "name",
        description="Search by: 'name', 'cid', 'smiles', or 'formula'",
    )


class PubChemTool(BaseTool):
    name: str = "pubchem"
    description: str = (
        "Search PubChem for chemical compounds — get molecular properties, "
        "structure, formula, weight, synonyms, and safety data. "
        "Free, no API key required."
    )
    args_schema: type = PubChemInput

    def _run(self, query: str, search_type: str = "name") -> str:
        try:
            cid = self._resolve_cid(query, search_type)
            if not cid:
                return f"No compound found for '{query}' (search_type={search_type})."

            props = self._get_properties(cid)
            synonyms = self._get_synonyms(cid)
            desc = self._get_description(cid)

            lines = [f"PubChem compound (CID {cid}):"]
            if props:
                lines.append(
                    f"  Formula: {props.get('MolecularFormula', '?')} | "
                    f"MW: {props.get('MolecularWeight', '?')} g/mol"
                )
                lines.append(
                    f"  IUPAC: {props.get('IUPACName', '?')}"
                )
                lines.append(
                    f"  SMILES: {props.get('CanonicalSMILES', '?')}"
                )
                lines.append(
                    f"  InChI: {props.get('InChI', '?')}"
                )
                xlogp = props.get("XLogP")
                if xlogp is not None:
                    lines.append(f"  XLogP: {xlogp} | TPSA: {props.get('TPSA', '?')} Å²")
                lines.append(
                    f"  H-Bond Donors: {props.get('HBondDonorCount', '?')} | "
                    f"Acceptors: {props.get('HBondAcceptorCount', '?')} | "
                    f"Rotatable: {props.get('RotatableBondCount', '?')}"
                )
            if synonyms:
                lines.append(f"  Synonyms: {', '.join(synonyms[:5])}")
            if desc:
                lines.append(f"  Description: {desc[:300]}")
            lines.append(
                f"  URL: https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
            )
            return "\n".join(lines)

        except requests.exceptions.HTTPError as e:
            return f"PubChem error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"PubChem error: {e}"

    def _resolve_cid(self, query: str, search_type: str) -> str | None:
        if search_type == "cid":
            return query
        ns = {"name": "name", "smiles": "smiles", "formula": "fastformula"}.get(
            search_type, "name"
        )
        resp = requests.get(
            f"{_PUG_BASE}/compound/{ns}/{requests.utils.quote(query, safe='')}/cids/JSON",
            timeout=15,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        cids = resp.json().get("IdentifierList", {}).get("CID", [])
        return str(cids[0]) if cids else None

    def _get_properties(self, cid: str) -> dict:
        props_list = (
            "MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES,"
            "InChI,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,RotatableBondCount"
        )
        resp = requests.get(
            f"{_PUG_BASE}/compound/cid/{cid}/property/{props_list}/JSON",
            timeout=15,
        )
        if resp.status_code != 200:
            return {}
        table = resp.json().get("PropertyTable", {}).get("Properties", [])
        return table[0] if table else {}

    def _get_synonyms(self, cid: str) -> list:
        resp = requests.get(
            f"{_PUG_BASE}/compound/cid/{cid}/synonyms/JSON", timeout=10
        )
        if resp.status_code != 200:
            return []
        info = resp.json().get("InformationList", {}).get("Information", [])
        return info[0].get("Synonym", []) if info else []

    def _get_description(self, cid: str) -> str:
        resp = requests.get(
            f"{_PUG_BASE}/compound/cid/{cid}/description/JSON", timeout=10
        )
        if resp.status_code != 200:
            return ""
        info = resp.json().get("InformationList", {}).get("Information", [])
        for item in info:
            desc = item.get("Description", "")
            if desc:
                return desc
        return ""
