"""
Motor de reglas CIE-10 Vol. 2 (Versión 2018) para la selección de la causa básica de defunción.

Implementa los pasos SP1-SP8 para seleccionar el punto de inicio tentativo,
y M1-M4 para las modificaciones de la causa básica provisional.

Referencia: CIE-10 Volumen 2 - Instrucciones para el uso, Sección 4.2.
"""

from __future__ import annotations
import re
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# Utilidades de clasificación CIE-10
# ──────────────────────────────────────────────────────────────────────────────

def _nums(code: str) -> int:
    m = re.search(r"\d+", code)
    return int(m.group()) if m else 0


def get_chapter(code: str) -> str:
    if not code: return ""
    c = code.upper().strip()
    L = c[0]
    n = _nums(c)
    if L in ("A", "B"): return "I"
    if L == "C": return "II"
    if L == "D": return "II" if n <= 48 else "III"
    if L == "E": return "IV"
    if L == "F": return "V"
    if L == "G": return "VI"
    if L == "H": return "VII" if n <= 59 else "VIII"
    if L == "I": return "IX"
    if L == "J": return "X"
    if L == "K": return "XI"
    if L == "L": return "XII"
    if L == "M": return "XIII"
    if L == "N": return "XIV"
    if L == "O": return "XV"
    if L == "P": return "XVI"
    if L == "Q": return "XVII"
    if L == "R": return "XVIII"
    if L in ("S", "T"): return "XIX"
    if L in ("V", "W", "X", "Y"): return "XX"
    if L == "Z": return "XXI"
    return "UNKNOWN"


def is_ill_defined(code: str) -> bool:
    """SP7: Condiciones mal definidas (Capítulo XVIII), con excepciones de la versión 2018."""
    if not code: return False
    c = code.upper()
    # Excepciones 2018: R57.2, R65.0, R65.1, R95 no son mal definidas.
    if c in ("R57.2", "R65.0", "R65.1", "R95"): return False
    return c.startswith("R") and _nums(c) <= 94


def is_senility(code: str) -> bool:
    """Regla a): Senilidad y afecciones inespecíficas que no deben ser causa de condiciones específicas."""
    if not code: return False
    c = code.upper().strip()
    # R54: Senilidad; R99: Causa de muerte mal definida y no especificada;
    # R96.x: Muerte instantánea / por causa desconocida
    return c[:3] in {"R54", "R99", "R96"}


# ── CORRECCIÓN 4: is_trivial() expandida con todos los rangos del Anexo 7.4 ──
# Categorías de 3 caracteres correspondientes a traumatismos superficiales
_TRIVIAL_3CHAR = frozenset({
    "S00",  # Traumatismo superficial de la cabeza
    "S10",  # Traumatismo superficial del cuello
    "S20",  # Traumatismo superficial del tórax
    "S30",  # Traumatismo superficial del abdomen, región lumbar y pelvis
    "S40",  # Traumatismo superficial del hombro y del brazo
    "S50",  # Traumatismo superficial del codo y del antebrazo
    "S60",  # Traumatismo superficial de la muñeca y de la mano
    "S70",  # Traumatismo superficial de la cadera y del muslo
    "S80",  # Traumatismo superficial de la rodilla y de la pierna
    "S90",  # Traumatismo superficial del tobillo y del pie
    "T07",  # Traumatismos múltiples no especificados
})

def is_trivial(code: str) -> bool:
    """SP8: Afecciones poco probables de causar la muerte (Anexo 7.4)."""
    if not code: return False
    c = code.upper().strip()
    if c[0] == "Z": return True
    if c[:3] in _TRIVIAL_3CHAR: return True
    if c[:5] == "T14.0": return True  # Traumatismo superficial de región no especificada
    return False


def is_pregnancy_code(code: str) -> bool:
    return bool(code) and code.upper().startswith("O")


def is_external_cause(code: str) -> bool:
    return bool(code) and code.upper()[0] in ("V", "W", "X", "Y")


def is_injury_code(code: str) -> bool:
    return bool(code) and code.upper()[0] in ("S", "T")


def parse_duration_minutes(d_str: str) -> int:
    """Convierte un intervalo de tiempo a minutos aproximados para validación de secuencias."""
    if not d_str: return 0
    d_str = d_str.lower()
    m = re.search(r'(\d+)\s*(año|ano|mes|semana|dia|día|hora|min)', d_str)
    if not m: return 0
    val = int(m.group(1))
    unit = m.group(2)
    if 'año' in unit or 'ano' in unit: return val * 365 * 24 * 60
    if 'mes' in unit: return val * 30 * 24 * 60
    if 'semana' in unit: return val * 7 * 24 * 60
    if 'dia' in unit or 'día' in unit: return val * 24 * 60
    if 'hora' in unit: return val * 60
    if 'min' in unit: return val
    return 0


# ──────────────────────────────────────────────────────────────────────────────
# Validación de secuencias (Sección 4.2.3 y 4.2.4)
# ──────────────────────────────────────────────────────────────────────────────

def is_valid_sequence(cause_code: str, cause_dur: str, effect_code: str, effect_dur: str) -> bool:
    """
    Evalúa si cause_code puede ser la causa subyacente de effect_code.
    Implementa las secuencias rechazadas de la Sección 4.2.3 del Vol. 2.
    """
    if not cause_code or not effect_code: return False

    # Validación de duración (Secuencias Rechazadas k): la causa no puede durar menos que el efecto
    c_min = parse_duration_minutes(cause_dur)
    e_min = parse_duration_minutes(effect_dur)
    if c_min > 0 and e_min > 0 and c_min < e_min:
        return False

    c_chap = get_chapter(cause_code)
    e_chap = get_chapter(effect_code)

    # ── CORRECCIÓN 3: Regla a) — Senilidad no puede causar condición específica ──
    if is_senility(cause_code) and not is_ill_defined(effect_code):
        return False

    # Secuencias Rechazadas l) Causas externas (Cap. XX) debidas a otras afecciones
    if e_chap == "XX" and c_chap != "XX":
        # Excepción: Caídas (W00-W19) por baja densidad ósea (M80-M85)
        if effect_code.upper().startswith("W") and _nums(effect_code) <= 19:
            if cause_code.upper().startswith("M") and 80 <= _nums(cause_code) <= 85:
                return True
        return False

    # Secuencias Rechazadas m) Suicidio no puede ser resultado de otra afección
    if effect_code.upper().startswith("X") and 60 <= _nums(effect_code) <= 84:
        return False

    # Secuencias Rechazadas b) Tumores malignos no resultan de otras enfermedades (excep. VIH)
    if e_chap == "II":
        if cause_code.upper()[:3] in ("B20", "B21", "B22", "B23", "B24"): return True
        return False

    return True


# ── CORRECCIÓN 6: is_obvious_cause() extendida con relaciones del Vol. 2 ──
def is_obvious_cause(cause_code: str, effect_code: str) -> bool:
    """SP6: Reglas de causa obvia (Sección 4.2.4). cause_code es causa evidente de effect_code."""
    c = cause_code.upper()
    e = effect_code.upper()

    # Tumores primarios son causa obvia de secundarios/metástasis (C77-C79)
    if e.startswith("C") and 77 <= _nums(e) <= 79 and c.startswith("C") and not (77 <= _nums(c) <= 79):
        return True

    # VIH causa obvia de infecciones oportunistas (Capítulo I)
    if c[:3] in ("B20", "B21", "B22", "B23", "B24") and get_chapter(e) == "I":
        return True

    # Infección localizada es causa obvia de sepsis (A40-A41)
    if e.startswith("A") and 40 <= _nums(e) <= 41:
        c_chap = get_chapter(c)
        if c_chap in ("I", "XI", "XIV") or c[0] in ("J", "L", "M"):
            return True

    # Cirrosis/hepatitis crónica → encefalopatía hepática o insuficiencia hepática aguda
    if e[:3] in ("G92", "K72") and c[:3] in ("K70", "K71", "K73", "K74", "B18"):
        return True

    # Sepsis o deshidratación grave → insuficiencia renal aguda (N17)
    if e.startswith("N17") and c[:3] in ("A40", "A41", "E86"):
        return True

    # Hipertensión → hemorragia cerebral (I61-I62)
    if e.startswith("I") and 61 <= _nums(e) <= 62 and c[:3] == "I10":
        return True

    # Diabetes → complicaciones crónicas (nefropatía N18, retinopatía H36, neuropatía G63)
    if c[0] == "E" and 10 <= _nums(c) <= 14:
        if e[:3] in ("N18", "H36", "G63"):
            return True

    return False


# ──────────────────────────────────────────────────────────────────────────────
# Modificaciones M1: Vinculaciones e instrucciones especiales
# ──────────────────────────────────────────────────────────────────────────────

# ── CORRECCIÓN 5: _LINKAGE ampliado con pares faltantes del Vol. 2 ──
_LINKAGE: dict[frozenset, str] = {
    # Hipertensión + afectación renal
    frozenset({"I10", "N18"}): "I12.9",   # HTA + ERC → HTA con ERC
    frozenset({"I10", "N19"}): "I12.9",   # HTA + IR NE → HTA con IR
    frozenset({"I10", "N17"}): "I12.0",   # HTA + IRA → HTA con falla renal aguda
    # Hipertensión + afectación cardíaca
    frozenset({"I10", "I50"}): "I11.0",   # HTA + IC → HTA con IC
    frozenset({"I10", "I25"}): "I11.9",   # HTA + CC isquémica → HTA con CC
    # Hipertensión + cardíaca + renal
    frozenset({"I11", "N18"}): "I13.1",   # HTA CC + ERC → HTA CC+renal
    frozenset({"I11", "N17"}): "I13.1",   # HTA CC + IRA
    # Diabetes + nefropatía
    frozenset({"E10", "N18"}): "E10.2",   # DM1 + ERC → DM1 con nefropatía
    frozenset({"E10", "N17"}): "E10.2",   # DM1 + IRA
    frozenset({"E11", "N18"}): "E11.2",   # DM2 + ERC → DM2 con nefropatía
    frozenset({"E11", "N17"}): "E11.2",   # DM2 + IRA
    frozenset({"E14", "N18"}): "E14.2",   # DM NE + ERC
    frozenset({"E14", "N17"}): "E14.2",   # DM NE + IRA
    # Respiratorio
    frozenset({"J44", "J18"}): "J44.0",   # EPOC + neumonía → EPOC con infección aguda
    frozenset({"J45", "J18"}): "J45.0",   # Asma + neumonía → asma con infección aguda
    # Hepático
    frozenset({"K74", "K70"}): "K70.3",   # Cirrosis + enf. alcohólica hepática
    frozenset({"B18", "K74"}): "K74.6",   # Hepatitis crónica viral + cirrosis → cirrosis biliar
    # Neurológico
    frozenset({"G30", "F00"}): "F00.9",   # Alzheimer + demencia → demencia en Alzheimer
}

def apply_m1_linkage(tentative_cause: str, all_codes: list[str]) -> str:
    """Paso M1: Comprobar vinculaciones y combinaciones.
    Solo se aplica cuando la causa tentativa forma parte del par de vinculación (Sección 4.2.8).
    """
    cats = {c.upper()[:3] for c in all_codes if c}
    tent_cat = tentative_cause.upper()[:3]

    for key, combined in _LINKAGE.items():
        # La causa tentativa debe ser uno de los componentes del par
        if tent_cat in key and key.issubset(cats):
            return combined
    return tentative_cause


def apply_m2_specificity(tentative_cause: str, all_codes: list[str]) -> str:
    """Paso M2: Especificidad. Selecciona el código más específico de la misma afección."""
    cat = tentative_cause.upper()[:3]
    for code in all_codes:
        cu = code.upper()
        if cu.startswith(cat) and len(cu) > len(tentative_cause) and cu != tentative_cause:
            return cu
    return tentative_cause


# ──────────────────────────────────────────────────────────────────────────────
# Lógica Principal: Motor CIE-10 (SP1-SP8, M1-M4)
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_rows(raw_rows: list) -> list[dict]:
    rows = []
    for item in raw_rows:
        codes = []
        for e in item.get("codes", []):
            c = str(e.get("code", "")).strip().upper()
            if c: codes.append(c)
        if not codes and item.get("code"):
            c = str(item["code"]).strip().upper()
            if c: codes.append(c)
        if codes:
            rows.append({
                "line": str(item.get("line", "")),
                "interval": str(item.get("interval", "")),
                "codes": codes,
            })
    return rows

def analyze_certificate(data: dict) -> dict:
    steps_log = []
    def log(step: str, desc: str):
        steps_log.append({"step": step, "description": desc})

    part1_rows = _normalize_rows(data.get("part1", []))
    part2_rows = _normalize_rows(data.get("part2", []))

    all_codes = []
    for r in part1_rows + part2_rows:
        all_codes.extend(r["codes"])

    if not part1_rows:
        return {
            "selected_code": None, "step_determined": None, "steps_log": [],
            "justification": "Error: No se ingresaron causas en la Parte I del certificado."
        }

    log("INICIO", f"Certificado recibido: {sum(len(r['codes']) for r in part1_rows)} causa(s) en Parte I, "
                  f"{sum(len(r['codes']) for r in part2_rows)} en Parte II.")

    # ── Fase 1: Localizar el punto de inicio (SP1-SP8) ──
    tentative_cause = None
    step_det = ""

    def find_starting_point(ignored_codes: set) -> tuple[str, str]:
        valid_p1 = [r for r in part1_rows if any(c not in ignored_codes for c in r["codes"])]
        valid_all = [c for c in all_codes if c not in ignored_codes]

        if not valid_all:
            return "", ""

        # SP1: Una sola causa
        if len(valid_all) == 1:
            log("SP1", f"Una sola causa válida en el certificado: {valid_all[0]}.")
            return valid_all[0], "SP1"

        # SP2: Solamente una línea en la Parte 1
        if len(valid_p1) == 1:
            first_code = [c for c in valid_p1[0]["codes"] if c not in ignored_codes][0]
            log("SP2", f"Solamente una línea utilizada en Parte 1. Seleccionado: {first_code}.")
            return first_code, "SP2"

        # ── CORRECCIÓN 8: SP3 itera sobre todos los códigos de la línea más baja ──
        bottom_row = valid_p1[-1]
        bottom_codes = [c for c in bottom_row["codes"] if c not in ignored_codes]
        for candidate in bottom_codes:
            can_explain = True
            for r in valid_p1[:-1]:
                r_codes = [c for c in r["codes"] if c not in ignored_codes]
                if r_codes and not is_valid_sequence(candidate, bottom_row["interval"], r_codes[0], r["interval"]):
                    can_explain = False
                    break
            if can_explain:
                log("SP3", f"La afección más baja '{candidate}' puede explicar las superiores.")
                return candidate, "SP3"

        # ── CORRECCIÓN 1: SP4 evalúa cadena válida paso a paso (d→c→b→a) ──
        terminal_row = valid_p1[0]
        terminal_code = [c for c in terminal_row["codes"] if c not in ignored_codes]
        if not terminal_code:
            return "", ""
        terminal_code = terminal_code[0]

        # Buscar la raíz de una cadena válida que llegue hasta la línea (a) paso a paso
        for start_idx in range(len(valid_p1) - 1, 0, -1):
            rcodes = [c for c in valid_p1[start_idx]["codes"] if c not in ignored_codes]
            if not rcodes:
                continue
            chain_ok = True
            for i in range(start_idx, 0, -1):
                lower_row = valid_p1[i]
                upper_row = valid_p1[i - 1]
                lower_code = [c for c in lower_row["codes"] if c not in ignored_codes]
                upper_code = [c for c in upper_row["codes"] if c not in ignored_codes]
                if not lower_code or not upper_code:
                    chain_ok = False
                    break
                if not is_valid_sequence(lower_code[0], lower_row["interval"], upper_code[0], upper_row["interval"]):
                    chain_ok = False
                    break
            if chain_ok:
                log("SP4", f"Secuencia válida encontrada: '{rcodes[0]}' origina la cadena hasta afección terminal '{terminal_code}'.")
                return rcodes[0], "SP4"

        # SP5: Ninguna secuencia en Parte 1 → seleccionar afección terminal
        log("SP5", f"No hay secuencias válidas. Se selecciona afección terminal: {terminal_code}.")
        return terminal_code, "SP5"

    ignored = set()
    while True:
        tentative_cause, step_det = find_starting_point(ignored)
        if not tentative_cause:
            break

        # SP6: Causa obvia
        for c in all_codes:
            if c != tentative_cause and is_obvious_cause(c, tentative_cause):
                log("SP6", f"Causa obvia: '{c}' es causa evidente de '{tentative_cause}'.")
                tentative_cause = c
                step_det = "SP6"
                break

        # SP7: Afecciones mal definidas
        if is_ill_defined(tentative_cause):
            others_not_ill = [c for c in all_codes if c not in ignored and not is_ill_defined(c)]
            if others_not_ill:
                log("SP7", f"'{tentative_cause}' es mal definida. Se ignora y se reinicia el ciclo.")
                ignored.add(tentative_cause)
                continue
            else:
                log("SP7", f"'{tentative_cause}' es mal definida, pero no hay mejores opciones.")

        # SP8: Afecciones poco probables de causar la muerte
        if is_trivial(tentative_cause):
            others_not_trivial = [c for c in all_codes if c not in ignored and not is_trivial(c)]
            if others_not_trivial:
                log("SP8", f"'{tentative_cause}' es improbable que cause la muerte. Se ignora y reinicia.")
                ignored.add(tentative_cause)
                continue

        break  # Fin del ciclo SP1-SP8

    # ── Fase 2: Modificaciones (M1-M4) ──
    if not tentative_cause:
        return {"selected_code": None, "steps_log": steps_log, "justification": "Error fatal."}

    # Bucle M3 (re-evaluar SP6, M1, M2 hasta estabilización)
    previous_cause = ""
    while tentative_cause != previous_cause:
        previous_cause = tentative_cause

        # M1: Instrucciones especiales y Vinculaciones
        new_m1 = apply_m1_linkage(tentative_cause, all_codes)
        if new_m1 != tentative_cause:
            log("M1", f"Vinculación/Instrucción especial: '{tentative_cause}' combinado como '{new_m1}'.")
            tentative_cause = new_m1
            step_det = "M1"

        # M2: Especificidad
        new_m2 = apply_m2_specificity(tentative_cause, all_codes)
        if new_m2 != tentative_cause:
            log("M2", f"Especificidad: '{tentative_cause}' se detalla más como '{new_m2}'.")
            tentative_cause = new_m2
            step_det = "M2"

        # M3: Volver a comprobar si hubo cambios
        if tentative_cause != previous_cause:
            log("M3", "La causa cambió en M1/M2. Re-evaluando (M3).")

    # M4: Instrucciones especiales finales (Violencia, Maternidad)
    sex = data.get("sex", "M")
    pregnancy = data.get("pregnancy", "N")
    violence = bool(data.get("violence", False))
    violence_type = data.get("violence_type", "")

    # ── CORRECCIÓN 2: M4 maternal aplica O99.8 efectivamente ──
    if pregnancy == "S" and sex == "F" and not is_pregnancy_code(tentative_cause):
        log("M4", f"Mortalidad materna: causa '{tentative_cause}' reclasificada a O99.8 (Cap. XV — Embarazo, parto y puerperio).")
        tentative_cause = "O99.8"
        step_det = "M4"

    if violence and not is_external_cause(tentative_cause):
        suggested = {"A": "W19", "S": "X84", "H": "Y09"}.get(violence_type, "Y34")
        log("M4", f"Muerte violenta sin causa externa especificada. Código asignado: {suggested}.")
        tentative_cause = suggested
        step_det = "M4"

    # ── CORRECCIÓN 7: Validación por edad — advertencia para códigos perinatales ──
    age = data.get("age")
    if age is not None and age > 0 and get_chapter(tentative_cause) == "XVI":
        log("VALIDACIÓN", f"Advertencia: código perinatal (Cap. XVI) '{tentative_cause}' seleccionado "
                          f"para un paciente de {age} año(s). Verificar que corresponda.")

    # Preparar el resultado
    lines = [f"Causa básica de defunción seleccionada: {tentative_cause}", ""]
    lines.append("Pasos aplicados (CIE-10 Vol. 2 - 2018):")
    for s in steps_log:
        marker = " ◄ DETERMINANTE" if s["step"] == step_det else ""
        lines.append(f"  [{s['step']}]{marker}  {s['description']}")

    return {
        "selected_code": tentative_cause,
        "step_determined": step_det,
        "steps_log": steps_log,
        "justification": "\n".join(lines)
    }
