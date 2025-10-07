"""
Specification parser for extracting equipment specifications from text.

Parses unstructured text to extract equipment specifications, performance data,
and technical parameters using pattern matching and NLP techniques.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class SpecificationMatch:
    """Container for a matched specification."""

    parameter: str
    value: Any
    unit: Optional[str]
    confidence: float
    context: str


class SpecificationParser:
    """Parse equipment specifications from unstructured text."""

    # Common unit patterns
    UNIT_PATTERNS = {
        "capacity": r"(tph|tpd|mtpa|kt/d|t/h|tonnes?\s*per\s*(hour|day))",
        "power": r"(kw|mw|hp|kilowatts?|megawatts?)",
        "length": r"(m|mm|cm|ft|in|inches?|feet|meters?|millimeters?)",
        "weight": r"(kg|t|tonnes?|lbs?|pounds?)",
        "speed": r"(rpm|m/s|ft/min|revolutions?\s*per\s*minute)",
        "pressure": r"(psi|kpa|mpa|bar)",
        "temperature": r"(°c|°f|celsius|fahrenheit)",
        "energy": r"(kwh/t|kwh\s*per\s*tonne?)",
        "percentage": r"(%|percent|pct)",
        "currency": r"(usd|cad|eur|\$|€)",
    }

    # Equipment type patterns
    EQUIPMENT_PATTERNS = {
        "crusher": r"(gyratory|cone|jaw|impact|roll)\s*(crusher|crushing)",
        "mill": r"(sag|ball|rod|ag|autogenous|semi-autogenous)\s*(mill|grinding)",
        "conveyor": r"(belt|overland|apron)\s*(conveyor|feeder)",
        "screen": r"(vibrating|banana|horizontal)\s*screen",
        "pump": r"(slurry|centrifugal|positive\s*displacement)\s*pump",
    }

    # Specification patterns
    SPEC_PATTERNS = {
        "capacity": [
            r"capacity[:\s]+(\d+(?:,\d{3})*(?:\.\d+)?)\s*("
            + UNIT_PATTERNS["capacity"]
            + ")",
            r"throughput[:\s]+(\d+(?:,\d{3})*(?:\.\d+)?)\s*("
            + UNIT_PATTERNS["capacity"]
            + ")",
            r"rated\s*at\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*("
            + UNIT_PATTERNS["capacity"]
            + ")",
        ],
        "power": [
            r"power[:\s]+(\d+(?:,\d{3})*(?:\.\d+)?)\s*(" + UNIT_PATTERNS["power"] + ")",
            r"motor[:\s]+(\d+(?:,\d{3})*(?:\.\d+)?)\s*(" + UNIT_PATTERNS["power"] + ")",
            r"installed\s*power[:\s]+(\d+(?:,\d{3})*(?:\.\d+)?)\s*("
            + UNIT_PATTERNS["power"]
            + ")",
        ],
        "diameter": [
            r"diameter[:\s]+(\d+(?:\.\d+)?)\s*(" + UNIT_PATTERNS["length"] + ")",
            r"dia\.?[:\s]+(\d+(?:\.\d+)?)\s*(" + UNIT_PATTERNS["length"] + ")",
            r"(\d+(?:\.\d+)?)\s*(" + UNIT_PATTERNS["length"] + ")\s*diameter",
        ],
        "length": [
            r"length[:\s]+(\d+(?:\.\d+)?)\s*(" + UNIT_PATTERNS["length"] + ")",
            r"(\d+(?:\.\d+)?)\s*(" + UNIT_PATTERNS["length"] + ")\s*long",
        ],
        "weight": [
            r"weight[:\s]+(\d+(?:,\d{3})*(?:\.\d+)?)\s*("
            + UNIT_PATTERNS["weight"]
            + ")",
            r"mass[:\s]+(\d+(?:,\d{3})*(?:\.\d+)?)\s*(" + UNIT_PATTERNS["weight"] + ")",
        ],
        "speed": [
            r"speed[:\s]+(\d+(?:\.\d+)?)\s*(" + UNIT_PATTERNS["speed"] + ")",
            r"operating\s*speed[:\s]+(\d+(?:\.\d+)?)\s*("
            + UNIT_PATTERNS["speed"]
            + ")",
        ],
        "css": [
            r"css[:\s]+(\d+(?:\.\d+)?)\s*(" + UNIT_PATTERNS["length"] + ")",
            r"closed\s*side\s*setting[:\s]+(\d+(?:\.\d+)?)\s*("
            + UNIT_PATTERNS["length"]
            + ")",
        ],
        "feed_opening": [
            r"feed\s*opening[:\s]+(\d+(?:\.\d+)?)\s*(" + UNIT_PATTERNS["length"] + ")",
            r"opening[:\s]+(\d+(?:\.\d+)?)\s*(" + UNIT_PATTERNS["length"] + ")",
        ],
    }

    # Manufacturer patterns
    MANUFACTURER_PATTERNS = [
        r"manufacturer[:\s]+([\w\s]+?)(?:\n|$)",
        r"(?:supplied|manufactured)\s*by[:\s]+([\w\s]+?)(?:\n|$)",
        r"(metso|sandvik|flsmidth|weir|thyssenkrupp|terex|mccloskey|kleemann)\b",
    ]

    # Model patterns
    MODEL_PATTERNS = [
        r"model[:\s]+([A-Z0-9\-\s]+?)(?:\n|$)",
        r"type[:\s]+([A-Z0-9\-\s]+?)(?:\n|$)",
        r"(superior|MP|CH|HP|GP|nordberg)\s*[A-Z]*\s*[\d\-]+",
    ]

    def __init__(self):
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Precompile regex patterns for efficiency."""
        compiled = {}
        for param, patterns in self.SPEC_PATTERNS.items():
            compiled[param] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise

    def parse_specifications(
        self, text: str, equipment_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse specifications from text.

        Args:
            text: Input text containing specifications
            equipment_type: Optional equipment type hint

        Returns:
            Dictionary of parsed specifications
        """
        specs = {
            "specifications": {},
            "metadata": {
                "confidence": 0.0,
                "matched_parameters": 0,
                "equipment_type": equipment_type,
            },
        }

        # Detect equipment type if not provided
        if not equipment_type:
            equipment_type = self._detect_equipment_type(text)
            specs["metadata"]["equipment_type"] = equipment_type

        # Extract manufacturer and model
        manufacturer = self._extract_manufacturer(text)
        if manufacturer:
            specs["specifications"]["manufacturer"] = manufacturer

        model = self._extract_model(text)
        if model:
            specs["specifications"]["model"] = model

        # Extract all specification parameters
        matches = []
        for param, patterns in self.compiled_patterns.items():
            match = self._find_parameter(text, param, patterns)
            if match:
                matches.append(match)
                specs["specifications"][match.parameter] = {
                    "value": match.value,
                    "unit": match.unit,
                    "confidence": match.confidence,
                }

        # Calculate overall confidence
        specs["metadata"]["matched_parameters"] = len(matches)
        if matches:
            avg_confidence = sum(m.confidence for m in matches) / len(matches)
            specs["metadata"]["confidence"] = round(avg_confidence, 2)

        return specs

    def _detect_equipment_type(self, text: str) -> Optional[str]:
        """Detect equipment type from text."""
        for eq_type, pattern in self.EQUIPMENT_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return eq_type
        return None

    def _extract_manufacturer(self, text: str) -> Optional[str]:
        """Extract manufacturer name."""
        for pattern in self.MANUFACTURER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                manufacturer = match.group(1).strip()
                # Clean up common suffixes
                manufacturer = re.sub(
                    r"\s+(inc|ltd|llc|corporation|corp)\.?$",
                    "",
                    manufacturer,
                    flags=re.IGNORECASE,
                )
                return manufacturer.title()
        return None

    def _extract_model(self, text: str) -> Optional[str]:
        """Extract model designation."""
        for pattern in self.MODEL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                model = (
                    match.group(0).strip()
                    if match.lastindex is None
                    else match.group(1).strip()
                )
                return model.upper()
        return None

    def _find_parameter(
        self, text: str, param_name: str, patterns: List[re.Pattern]
    ) -> Optional[SpecificationMatch]:
        """Find a specific parameter in text."""
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                # Extract value and unit
                value_str = match.group(1).replace(",", "")
                unit = match.group(2).strip().lower() if match.lastindex >= 2 else None

                # Convert to appropriate type
                try:
                    value = float(value_str)
                except ValueError:
                    value = value_str

                # Get context (surrounding text)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()

                # Calculate confidence based on pattern specificity
                confidence = (
                    0.9
                    if "capacity" in pattern.pattern or "power" in pattern.pattern
                    else 0.8
                )

                return SpecificationMatch(
                    parameter=param_name,
                    value=value,
                    unit=unit,
                    confidence=confidence,
                    context=context,
                )

        return None

    def parse_mill_specifications(self, text: str) -> Dict[str, Any]:
        """
        Specialized parser for mill specifications.

        Extracts mill-specific parameters like diameter x length, ball charge, etc.
        """
        specs = self.parse_specifications(text, "mill")

        # Extract mill dimensions (diameter x length format)
        dim_pattern = (
            r"(\d+(?:\.\d+)?)\s*(?:m|meters?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:m|meters?)"
        )
        dim_match = re.search(dim_pattern, text, re.IGNORECASE)

        if dim_match:
            specs["specifications"]["diameter_m"] = {
                "value": float(dim_match.group(1)),
                "unit": "m",
                "confidence": 0.95,
            }
            specs["specifications"]["length_m"] = {
                "value": float(dim_match.group(2)),
                "unit": "m",
                "confidence": 0.95,
            }

        # Extract mill speed (% critical)
        speed_pattern = r"(\d+(?:\.\d+)?)\s*%\s*critical"
        speed_match = re.search(speed_pattern, text, re.IGNORECASE)

        if speed_match:
            specs["specifications"]["critical_speed_pct"] = {
                "value": float(speed_match.group(1)),
                "unit": "%",
                "confidence": 0.9,
            }

        # Extract ball charge
        ball_pattern = r"ball\s*charge[:\s]+(\d+(?:\.\d+)?)\s*%"
        ball_match = re.search(ball_pattern, text, re.IGNORECASE)

        if ball_match:
            specs["specifications"]["ball_charge_pct"] = {
                "value": float(ball_match.group(1)),
                "unit": "%",
                "confidence": 0.9,
            }

        return specs

    def parse_crusher_specifications(self, text: str) -> Dict[str, Any]:
        """
        Specialized parser for crusher specifications.

        Extracts crusher-specific parameters like CSS, feed opening, reduction ratio.
        """
        specs = self.parse_specifications(text, "crusher")

        # Extract reduction ratio
        ratio_pattern = r"reduction\s*ratio[:\s]+(\d+(?:\.\d+)?)\s*:\s*1"
        ratio_match = re.search(ratio_pattern, text, re.IGNORECASE)

        if ratio_match:
            specs["specifications"]["reduction_ratio"] = {
                "value": float(ratio_match.group(1)),
                "unit": "ratio",
                "confidence": 0.9,
            }

        # Extract throw (for gyratory crushers)
        throw_pattern = (
            r"throw[:\s]+(\d+(?:\.\d+)?)\s*(" + self.UNIT_PATTERNS["length"] + ")"
        )
        throw_match = re.search(throw_pattern, text, re.IGNORECASE)

        if throw_match:
            specs["specifications"]["throw"] = {
                "value": float(throw_match.group(1)),
                "unit": throw_match.group(2).lower(),
                "confidence": 0.85,
            }

        # Extract eccentric speed
        eccentric_pattern = r"eccentric\s*speed[:\s]+(\d+(?:\.\d+)?)\s*rpm"
        eccentric_match = re.search(eccentric_pattern, text, re.IGNORECASE)

        if eccentric_match:
            specs["specifications"]["eccentric_speed_rpm"] = {
                "value": float(eccentric_match.group(1)),
                "unit": "rpm",
                "confidence": 0.9,
            }

        return specs

    def parse_conveyor_specifications(self, text: str) -> Dict[str, Any]:
        """
        Specialized parser for conveyor specifications.

        Extracts conveyor-specific parameters like belt width, speed, lift.
        """
        specs = self.parse_specifications(text, "conveyor")

        # Extract belt width
        width_pattern = (
            r"belt\s*width[:\s]+(\d+(?:\.\d+)?)\s*("
            + self.UNIT_PATTERNS["length"]
            + ")"
        )
        width_match = re.search(width_pattern, text, re.IGNORECASE)

        if width_match:
            specs["specifications"]["belt_width"] = {
                "value": float(width_match.group(1)),
                "unit": width_match.group(2).lower(),
                "confidence": 0.9,
            }

        # Extract belt speed
        belt_speed_pattern = (
            r"belt\s*speed[:\s]+(\d+(?:\.\d+)?)\s*(" + self.UNIT_PATTERNS["speed"] + ")"
        )
        belt_speed_match = re.search(belt_speed_pattern, text, re.IGNORECASE)

        if belt_speed_match:
            specs["specifications"]["belt_speed"] = {
                "value": float(belt_speed_match.group(1)),
                "unit": belt_speed_match.group(2).lower(),
                "confidence": 0.9,
            }

        # Extract lift/vertical rise
        lift_pattern = (
            r"(?:lift|vertical\s*rise)[:\s]+(\d+(?:\.\d+)?)\s*("
            + self.UNIT_PATTERNS["length"]
            + ")"
        )
        lift_match = re.search(lift_pattern, text, re.IGNORECASE)

        if lift_match:
            specs["specifications"]["lift"] = {
                "value": float(lift_match.group(1)),
                "unit": lift_match.group(2).lower(),
                "confidence": 0.85,
            }

        return specs

    def extract_all_specifications(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract all equipment specifications from a PDF.

        Returns:
            List of specification dictionaries, one per equipment found
        """
        text = self.extract_text_from_pdf(pdf_path)

        # Split text by common section delimiters
        sections = self._split_into_sections(text)

        all_specs = []
        for section in sections:
            # Try to identify equipment type
            eq_type = self._detect_equipment_type(section)

            if eq_type:
                # Use specialized parser if available
                if eq_type == "mill":
                    specs = self.parse_mill_specifications(section)
                elif eq_type == "crusher":
                    specs = self.parse_crusher_specifications(section)
                elif eq_type == "conveyor":
                    specs = self.parse_conveyor_specifications(section)
                else:
                    specs = self.parse_specifications(section, eq_type)

                if specs["specifications"]:
                    all_specs.append(specs)

        logger.info(f"Extracted specifications for {len(all_specs)} equipment items")
        return all_specs

    def _split_into_sections(self, text: str) -> List[str]:
        """Split text into sections by equipment or headings."""
        # Common section delimiters
        delimiters = [
            r"\n\d+\.\s+",  # Numbered sections (1. 2. 3.)
            r"\n[A-Z][A-Z\s]+\n",  # ALL CAPS HEADINGS
            r"\n={3,}\n",  # Separator lines
            r"\nEquipment\s+\d+:",  # Equipment labels
        ]

        # Combine delimiters
        delimiter_pattern = "|".join(delimiters)
        sections = re.split(delimiter_pattern, text)

        # Filter out very short sections (likely noise)
        return [s.strip() for s in sections if len(s.strip()) > 100]
