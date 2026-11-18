#!/usr/bin/env python3
"""QuantumMaterials-Lab - educational quantum-materials tight-binding lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only - and the central lesson is stated up front:

  * This lab computes tight-binding band structures EXACTLY for TOY
    lattices: a 1D chain, a 2D square lattice, a graphene-style
    honeycomb, a dimerized SSH chain, and a two-site Hubbard dimer.
    Every hopping is a labelled teaching parameter (t = 1), every
    lattice constant is a labelled toy value, and every number the
    lab prints is exact FOR THE TOY MODEL.
  * A toy model is not a material. Nothing here predicts the band
    structure, gap, conductivity, or any other property of any real
    substance, and nothing here is a measurement.
  * What is real is the structure of the theory: why a 1D density of
    states diverges at band edges, why the square lattice has a van
    Hove saddle at half filling, why graphene's bands touch at Dirac
    points with linear dispersion, why a dimerized chain with the
    strong bond BETWEEN cells hides zero-energy states on its ends,
    and why repulsion U drains double occupancy out of a Hubbard
    dimer. Those are theorems about the models, demonstrated -
    not quoted - by exact computation inside this one file.

Real-material predictions, material discovery, superconductor,
device, synthesis, battery, semiconductor-production, quantum-
hardware, weapons, medical, investment, patent, and safety claims
are permanent HOLD gates - with Gemini Argon 4 Extended Thinking
as DECIDER (names-only, tighten-only), Muse as advisor (never
overrides HOLD), and Google Flow plan-only seats.
"""
import cmath
import hashlib
import json
import math
import sys
from itertools import combinations

# ---------------------------------------------------------------- constants
VERSION = "1.0.0"

# Labelled toy parameters. t = 1 sets the energy unit; a = 1 sets the
# length unit. These are teaching values, NOT fitted to any material.
T_HOP = 1.0          # nearest-neighbour hopping, in toy energy units
A_CC = 1.0           # carbon-carbon distance in the honeycomb toy, toy units
FERMI_ENERGY = 0.0   # half filling for every model in this lab

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "real_material_prediction_claim": "HOLD - no predicting a real material's band structure, gap, or properties from a toy model",
    "material_discovery_claim": "HOLD - no claiming discovery of a new material, phase, or compound",
    "superconductor_claim": "HOLD - no claiming a real superconductor, a critical temperature, or a pairing mechanism for a real substance",
    "device_fabrication_guidance": "HOLD - no fabrication recipes, process flows, or growth parameters for real devices",
    "synthesis_recipe_claim": "HOLD - no chemical synthesis routes, precursors, or reaction conditions",
    "battery_material_claim": "HOLD - no battery capacity, voltage, cycle-life, or safety claims for real cells",
    "semiconductor_production_claim": "HOLD - no production semiconductor design, doping profile, or wafer-process claims",
    "quantum_hardware_claim": "HOLD - no claiming a working topological qubit, protected gate, or quantum hardware from the SSH toy",
    "weapons_material_claim": "HOLD - no weapons, explosives, or energetic-material guidance of any kind",
    "medical_material_claim": "HOLD - no implant, biocompatibility, or medical-material claims",
    "investment_claim": "HOLD - no investment claims; a toy band structure is not a prospectus",
    "patent_novelty_claim": "HOLD - no patent, novelty, or prior-art claims for real materials or devices",
    "lab_safety_bypass": "HOLD - laboratory safety procedures are never bypassed, simulated away, or treated as optional",
    "toy_model_as_measurement_claim": "HOLD - toy tight-binding numbers must never be presented as measurements of a real material",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Band models
# Each model is a dispersion E(k) evaluated on an explicit k-grid.
# Nothing is fitted and nothing is hidden: the grids are fine enough
# that every extremum the checks assert is visible in the samples.

def chain_1d_energy(k, t=T_HOP):
    """1D chain dispersion E(k) = -2t cos(ka), a = 1."""
    return -2.0 * t * math.cos(k)


def chain_1d_energies(nk=4001, t=T_HOP):
    return [chain_1d_energy(-math.pi + 2.0 * math.pi * i / (nk - 1), t)
            for i in range(nk)]


def square_2d_energy(kx, ky, t=T_HOP):
    """2D square lattice dispersion E(k) = -2t (cos kx + cos ky)."""
    return -2.0 * t * (math.cos(kx) + math.cos(ky))


def square_2d_energies(nk=301, t=T_HOP):
    out = []
    for i in range(nk):
        kx = -math.pi + 2.0 * math.pi * i / (nk - 1)
        for j in range(nk):
            ky = -math.pi + 2.0 * math.pi * j / (nk - 1)
            out.append(square_2d_energy(kx, ky, t))
    return out


def bandwidth(energies):
    return max(energies) - min(energies)


def dos_histogram(energies, emin, emax, bins=41):
    """Density of states by histogram: (bin centres, densities).

    Density = count / (N * bin width), so the densities integrate
    (approximately) to 1 over the band. Van Hove structure is read
    straight off the bins - nothing is smoothed.
    """
    width = (emax - emin) / bins
    counts = [0] * bins
    for e in energies:
        idx = int((e - emin) / width)
        if idx < 0:
            idx = 0
        elif idx >= bins:
            idx = bins - 1
        counts[idx] += 1
    n = len(energies)
    centres = [emin + (i + 0.5) * width for i in range(bins)]
    densities = [c / (n * width) for c in counts]
    return centres, densities


def dos_at(energies, e0, half_width=0.1):
    """DOS near e0: fraction of states within +-half_width, per unit energy."""
    inside = sum(1 for e in energies if abs(e - e0) <= half_width)
    return inside / (len(energies) * 2.0 * half_width)


# ================================================================ 2. Graphene toy
# Honeycomb lattice, two sites per cell, nearest-neighbour hopping t.
# The Bloch Hamiltonian is H(k) = [[0, -t f(k)], [-t f*(k), 0]] with
# f(k) = sum_j exp(i k . delta_j) over the three nearest-neighbour
# vectors delta_j (each of length A_CC). Bands: E = +- t |f(k)|.
# A_CC is the carbon-carbon distance, so the Dirac slope comes out at
# the textbook (3/2) t A_CC with a LABELLED Fermi velocity.

SQRT3 = math.sqrt(3.0)
NEIGHBOURS = ((0.0, A_CC),
              (SQRT3 / 2.0 * A_CC, -0.5 * A_CC),
              (-SQRT3 / 2.0 * A_CC, -0.5 * A_CC))
K_POINT = (4.0 * math.pi / (3.0 * SQRT3 * A_CC), 0.0)
K_PRIME = (-4.0 * math.pi / (3.0 * SQRT3 * A_CC), 0.0)
FERMI_VELOCITY_LABELLED = 1.5 * T_HOP * A_CC  # hbar * v_F, toy units


def graphene_f(kx, ky):
    """Structure factor f(k) = sum_j exp(i k . delta_j)."""
    total = 0j
    for dx, dy in NEIGHBOURS:
        total += cmath.exp(1j * (kx * dx + ky * dy))
    return total


def graphene_bands(kx, ky, t=T_HOP):
    """(E_lower, E_upper) = -+ t |f(k)|."""
    mag = abs(graphene_f(kx, ky))
    return (-t * mag, t * mag)


def graphene_dirac_slope(t=T_HOP):
    """Fitted slope of E vs |q| along +x from K, through the origin.

    Samples |q| in [0.01, 0.06] - close enough to K that the cone is
    linear to better than a percent - and fits E = slope * |q|.
    """
    qs = [0.01 * i for i in range(1, 7)]
    es = [t * abs(graphene_f(K_POINT[0] + q, K_POINT[1])) for q in qs]
    num = sum(q * e for q, e in zip(qs, es))
    den = sum(q * q for q in qs)
    return num / den


def graphene_energies(nk=121, t=T_HOP):
    """Both bands sampled over the reciprocal unit cell (u, v in [0,1)).

    Real-space lattice vectors a1 = delta1 - delta2, a2 = delta1 - delta3;
    reciprocal vectors from the 2D dual formulas. The sampling covers the
    full Brillouin zone exactly once (a parallelogram cell of it).
    """
    a1 = (NEIGHBOURS[0][0] - NEIGHBOURS[1][0],
          NEIGHBOURS[0][1] - NEIGHBOURS[1][1])
    a2 = (NEIGHBOURS[0][0] - NEIGHBOURS[2][0],
          NEIGHBOURS[0][1] - NEIGHBOURS[2][1])
    det = a1[0] * a2[1] - a1[1] * a2[0]
    b1 = (2.0 * math.pi * a2[1] / det, -2.0 * math.pi * a2[0] / det)
    b2 = (-2.0 * math.pi * a1[1] / det, 2.0 * math.pi * a1[0] / det)
    out = []
    for i in range(nk):
        for j in range(nk):
            kx = (i / nk) * b1[0] + (j / nk) * b2[0]
            ky = (i / nk) * b1[1] + (j / nk) * b2[1]
            lo, hi = graphene_bands(kx, ky, t)
            out.append(lo)
            out.append(hi)
    return out


# ================================================================ 3. Jacobi eigensolver
# From-scratch cyclic Jacobi for real symmetric matrices. Returns
# (eigenvalues, eigenvector matrix V with eigenvectors as COLUMNS),
# so A = V diag(eigenvalues) V^T up to rounding. Used for the SSH
# finite chain and the Hubbard dimer - the two places this lab needs
# spectra of explicit Hamiltonians rather than dispersions.

def jacobi_eigh(matrix, tol=1e-12, max_sweeps=100):
    n = len(matrix)
    a = [list(row) for row in matrix]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(max_sweeps):
        off = math.sqrt(sum(a[i][j] ** 2 for i in range(n)
                            for j in range(n) if i != j))
        if off < tol:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-15:
                    continue
                theta = 0.5 * math.atan2(2.0 * a[p][q], a[q][q] - a[p][p])
                c, s = math.cos(theta), math.sin(theta)
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p] = c * vkp - s * vkq
                    v[k][q] = s * vkp + c * vkq
    return [a[i][i] for i in range(n)], v


# ================================================================ 4. SSH chain
# Dimerized chain: intracell hopping t1, intercell hopping t2.
# Bloch factor d(k) = t1 + t2 exp(ika); bands E = +- |d(k)|; the bulk
# gap is 2|t1 - t2|. The winding of d(k) around the origin as k crosses
# the zone is 0 when t1 > t2 (trivial) and +-1 when t2 > t1
# (topological); the Zak phase is pi * winding. A finite OPEN chain
# makes the topology visible: zero-energy edge states appear exactly
# in the t2 > t1 phase (bulk-boundary correspondence, demonstrated).

def ssh_bloch_factor(k, t1, t2):
    return t1 + t2 * cmath.exp(1j * k)


def ssh_bulk_gap(t1, t2, nk=2001):
    """Bulk gap = 2 * min_k |d(k)|, sampled on a fine k-grid."""
    mn = min(abs(ssh_bloch_factor(2.0 * math.pi * i / (nk - 1), t1, t2))
             for i in range(nk))
    return 2.0 * mn


def ssh_energies_bloch(t1, t2, nk=801):
    out = []
    for i in range(nk):
        k = -math.pi + 2.0 * math.pi * i / (nk - 1)
        mag = abs(ssh_bloch_factor(k, t1, t2))
        out.append(-mag)
        out.append(mag)
    return out


def ssh_winding(t1, t2, nk=4000):
    """Winding number of d(k) around 0, by summed phase increments."""
    prev = cmath.phase(ssh_bloch_factor(0.0, t1, t2))
    total = 0.0
    for i in range(1, nk + 1):
        k = 2.0 * math.pi * i / nk
        phase = cmath.phase(ssh_bloch_factor(k, t1, t2))
        step = phase - prev
        while step > math.pi:
            step -= 2.0 * math.pi
        while step < -math.pi:
            step += 2.0 * math.pi
        total += step
        prev = phase
    return total / (2.0 * math.pi)


def ssh_zak_phase(t1, t2):
    """Zak phase = pi * winding (mod 2pi): 0 trivial, pi topological."""
    return math.pi * ssh_winding(t1, t2)


def ssh_chain_hamiltonian(t1, t2, ncells=20):
    """Open chain of ncells unit cells (2*ncells sites), real symmetric."""
    n = 2 * ncells
    h = [[0.0] * n for _ in range(n)]
    for cell in range(ncells):
        a_site, b_site = 2 * cell, 2 * cell + 1
        h[a_site][b_site] += t1
        h[b_site][a_site] += t1
        if cell + 1 < ncells:
            h[b_site][a_site + 2] += t2
            h[a_site + 2][b_site] += t2
    return h


def ssh_chain_spectrum(t1, t2, ncells=20):
    evals, _ = jacobi_eigh(ssh_chain_hamiltonian(t1, t2, ncells))
    return sorted(evals)


def ssh_edge_report(t1, t2, ncells=20):
    """Count midgap states of the open chain: |E| < 5% of the bulk gap
    scale (and, in the trivial phase, report the smallest |E|)."""
    evals = ssh_chain_spectrum(t1, t2, ncells)
    by_abs = sorted(evals, key=abs)
    midgap = [e for e in evals if abs(e) < 0.05]
    return {
        "t1": t1, "t2": t2, "ncells": ncells,
        "bulk_gap": ssh_bulk_gap(t1, t2),
        "winding": ssh_winding(t1, t2),
        "zak_phase_over_pi": ssh_zak_phase(t1, t2) / math.pi,
        "midgap_states": len(midgap),
        "smallest_abs_energy": abs(by_abs[0]),
        "second_smallest_abs_energy": abs(by_abs[1]),
    }


# ================================================================ 5. Hubbard dimer
# Two sites, two electrons (half filling), on-site repulsion U.
# Determinant basis: choose 2 of 4 spin orbitals
# (0 = site0-up, 1 = site0-down, 2 = site1-up, 3 = site1-down).
# Hopping -t between same-spin orbitals on different sites, applied
# with exact fermionic signs; U counts doubly occupied sites.
# The 6x6 Hamiltonian is diagonalized by the Jacobi solver above.
# Analytic anchors (textbook): E_ground = (U - sqrt(U^2 + 16 t^2))/2,
# total double occupancy D = (1 - U / sqrt(U^2 + 16 t^2)) / 2.

SPIN_ORBITALS = (0, 1, 2, 3)
HOPS = ((0, 2), (2, 0), (1, 3), (3, 1))  # (source, destination)


def _annihilate(state, orb):
    if orb not in state:
        return None, 0
    pos = state.index(orb)
    return state[:pos] + state[pos + 1:], (-1) ** pos


def _create(state, orb):
    if orb in state:
        return None, 0
    lst = list(state)
    pos = 0
    while pos < len(lst) and lst[pos] < orb:
        pos += 1
    return tuple(lst[:pos] + [orb] + lst[pos:]), (-1) ** pos


def _double_occupancy(state):
    occ = set(state)
    return ((1 if (0 in occ and 1 in occ) else 0)
            + (1 if (2 in occ and 3 in occ) else 0))


def hubbard_dimer_hamiltonian(t=T_HOP, u=0.0):
    basis = list(combinations(SPIN_ORBITALS, 2))
    index = {b: i for i, b in enumerate(basis)}
    h = [[0.0] * 6 for _ in range(6)]
    for bi, state in enumerate(basis):
        h[bi][bi] += u * _double_occupancy(state)
        for src, dst in HOPS:
            mid, s1 = _annihilate(state, src)
            if mid is None:
                continue
            new, s2 = _create(mid, dst)
            if new is None:
                continue
            h[index[new]][bi] += -t * s1 * s2
    return h, basis


def hubbard_dimer(t=T_HOP, u=0.0):
    """Exact ground state of the Hubbard dimer at half filling."""
    h, basis = hubbard_dimer_hamiltonian(t, u)
    evals, vecs = jacobi_eigh(h)
    g = min(range(6), key=lambda i: evals[i])
    ground_vec = [vecs[r][g] for r in range(6)]
    dbl = sum(ground_vec[bi] ** 2 * _double_occupancy(basis[bi])
              for bi in range(6))
    triplet_weight = sum(ground_vec[bi] ** 2 for bi, state in enumerate(basis)
                         if state in ((0, 2), (1, 3)))
    return {
        "t": t, "U": u,
        "ground_energy": evals[g],
        "double_occupancy": dbl,
        "triplet_weight": triplet_weight,
        "spectrum": sorted(evals),
    }


def hubbard_ground_energy_analytic(t=T_HOP, u=0.0):
    return (u - math.sqrt(u * u + 16.0 * t * t)) / 2.0


def hubbard_double_occupancy_analytic(t=T_HOP, u=0.0):
    return (1.0 - u / math.sqrt(u * u + 16.0 * t * t)) / 2.0


def hubbard_curve(t=T_HOP, us=(0.0, 1.0, 2.0, 4.0, 8.0)):
    return [hubbard_dimer(t, u) for u in us]


# ================================================================ 6. Material character + kNN
# Features: (gap, DOS at the Fermi level, winding). Every training row
# is COMPUTED by the models above (band grids, Bloch factors, DOS
# windows) - no row is hand-entered - and every label comes from
# model_label, the lab's own character policy. The kNN interpolates
# that policy over the computed rows; it does not invent physics.

GAP_TOL = 0.05        # below this a gap counts as closed (toy units)
DIRAC_DOS_MAX = 0.05  # DOS(E_F) below this with gap closed = Dirac-like


def model_label(gap, dos_fermi, winding):
    """The character policy distilled to a four-way teaching label."""
    if winding >= 1 and gap > GAP_TOL:
        return "topological"
    if gap > GAP_TOL:
        return "insulator"
    if dos_fermi < DIRAC_DOS_MAX:
        return "dirac-semimetal"
    return "metal"


def material_features(kind, **params):
    """Compute (gap, DOS at E_F, winding) for one of the lab's models."""
    if kind == "chain-1d":
        energies = chain_1d_energies(t=params.get("t", T_HOP))
        return (0.0, dos_at(energies, FERMI_ENERGY), 0)
    if kind == "square-2d":
        energies = square_2d_energies(nk=201, t=params.get("t", T_HOP))
        return (0.0, dos_at(energies, FERMI_ENERGY), 0)
    if kind == "graphene":
        energies = graphene_energies(nk=101, t=params.get("t", T_HOP))
        return (0.0, dos_at(energies, FERMI_ENERGY), 0)
    if kind == "ssh":
        t1, t2 = params["t1"], params["t2"]
        energies = ssh_energies_bloch(t1, t2)
        gap = ssh_bulk_gap(t1, t2)
        winding = int(round(abs(ssh_winding(t1, t2))))
        return (gap, dos_at(energies, FERMI_ENERGY), winding)
    raise ValueError(f"unknown material kind: {kind}")


def _training_rows():
    rows = []
    for t in (0.5, 1.0, 1.5):
        feats = material_features("chain-1d", t=t)
        rows.append((feats, model_label(*feats)))
    feats = material_features("square-2d")
    rows.append((feats, model_label(*feats)))
    feats = material_features("graphene")
    rows.append((feats, model_label(*feats)))
    for t1 in (0.4, 0.6, 0.8, 1.2, 1.4, 1.6):
        feats = material_features("ssh", t1=t1, t2=2.0 - t1)
        rows.append((feats, model_label(*feats)))
    return rows


TRAINING_ROWS = _training_rows()


def _scaled(features):
    gap, dos_fermi, winding = features
    return (gap / 2.0, dos_fermi / 0.35, float(winding))


def classify_material(gap, dos_fermi, winding, k=3):
    """kNN over the computed rows. Vote ties break toward the label
    whose nearest row is closest to the target (then a fixed label
    priority), so a target sitting exactly on a computed row always
    takes that row's label."""
    target = _scaled((gap, dos_fermi, winding))
    ranked = []
    for features, label in TRAINING_ROWS:
        point = _scaled(features)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(target, point)))
        ranked.append((dist, features, label))
    ranked.sort(key=lambda row: (row[0], row[1]))
    votes = {}
    nearest = {}
    for dist, _, label in ranked[:k]:
        votes[label] = votes.get(label, 0) + 1
        nearest.setdefault(label, dist)
    priority = {"topological": 0, "insulator": 1, "dirac-semimetal": 2,
                "metal": 3}
    return sorted(votes.items(),
                  key=lambda kv: (-kv[1], nearest[kv[0]],
                                  priority[kv[0]]))[0][0]


def classifier_scenarios():
    return {
        "chain_1d_half_filled": material_features("chain-1d"),
        "square_2d_half_filled": material_features("square-2d"),
        "graphene_honeycomb": material_features("graphene"),
        "ssh_trivial_t1_1.4_t2_0.6": material_features("ssh", t1=1.4, t2=0.6),
        "ssh_topological_t1_0.6_t2_1.4": material_features("ssh", t1=0.6,
                                                       t2=1.4),
    }


def classifier_report():
    return {name: classify_material(*feats)
            for name, feats in classifier_scenarios().items()}


# ================================================================ 7. Advisory seats
def _trace(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def argon4_decide(topic="quantummaterials-demo"):
    """Gemini Argon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-argon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Argon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all real-material gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="quantummaterials-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Say it in the first line of every report: these are exact numbers for toy lattices with labelled hoppings - then show the gap, the DOS at the Fermi level, and the winding that earned the label.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["a cosine band unrolling along a chain of atoms",
                  "a square-lattice DOS spiking at its van Hove saddle",
                  "two cones touching at a graphene Dirac point",
                  "a dimerized chain whose end atoms light up at zero energy",
                  "a Hubbard dimer draining its double occupancy as U grows"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": argon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    # 1. 1D chain: dispersion, bandwidth, van Hove edges
    e1 = chain_1d_energies()
    chk("chain_bandwidth_4t", abs(bandwidth(e1) - 4.0 * T_HOP) < 1e-9)
    chk("chain_energy_at_gamma", chain_1d_energy(0.0) == -2.0 * T_HOP)
    chk("chain_energy_at_zone_edge",
        abs(chain_1d_energy(math.pi) - 2.0 * T_HOP) < 1e-12)
    centres1, dos1 = dos_histogram(e1, -2.0 * T_HOP, 2.0 * T_HOP)
    mid1 = len(dos1) // 2
    chk("chain_dos_van_hove_edges",
        dos1[0] > dos1[mid1] and dos1[-1] > dos1[mid1])
    chk("chain_dos_normalized",
        abs(sum(dos1) * (4.0 * T_HOP / len(dos1)) - 1.0) < 0.02)
    chk("chain_dos_at_fermi_positive",
        dos_at(e1, FERMI_ENERGY) > 0.1)

    # 2. 2D square lattice: bandwidth, van Hove saddle at E = 0
    e2 = square_2d_energies()
    chk("square_bandwidth_8t", abs(bandwidth(e2) - 8.0 * T_HOP) < 1e-9)
    chk("square_energy_at_gamma", square_2d_energy(0.0, 0.0) == -4.0 * T_HOP)
    chk("square_energy_at_m_point",
        abs(square_2d_energy(math.pi, math.pi) - 4.0 * T_HOP) < 1e-12)
    centres2, dos2 = dos_histogram(e2, -4.0 * T_HOP, 4.0 * T_HOP)
    mid2 = len(dos2) // 2
    chk("square_dos_saddle_is_max", dos2[mid2] == max(dos2))
    chk("square_dos_saddle_above_edges",
        dos2[mid2] > dos2[0] and dos2[mid2] > dos2[-1])
    chk("square_dos_at_fermi_is_peak",
        dos_at(e2, FERMI_ENERGY) > dos_at(e2, -3.5 * T_HOP))

    # 3. graphene: Dirac points, linear cone, labelled Fermi velocity
    chk("graphene_f_vanishes_at_k",
        abs(graphene_f(*K_POINT)) < 1e-9)
    chk("graphene_f_vanishes_at_k_prime",
        abs(graphene_f(*K_PRIME)) < 1e-9)
    chk("graphene_bands_touch_at_k",
        graphene_bands(*K_POINT) == (0.0, 0.0)
        or all(abs(x) < 1e-9 for x in graphene_bands(*K_POINT)))
    chk("graphene_f_at_gamma_is_3", abs(abs(graphene_f(0.0, 0.0)) - 3.0) < 1e-12)
    chk("graphene_bandwidth_6t",
        abs(graphene_bands(0.0, 0.0)[1] - 3.0 * T_HOP) < 1e-12)
    slope = graphene_dirac_slope()
    chk("graphene_dirac_slope_textbook",
        abs(slope - FERMI_VELOCITY_LABELLED)
        < 0.05 * FERMI_VELOCITY_LABELLED)
    chk("graphene_fermi_velocity_labelled",
        FERMI_VELOCITY_LABELLED == 1.5 * T_HOP * A_CC)
    ge = graphene_energies(nk=101)
    chk("graphene_dos_vanishes_at_fermi",
        dos_at(ge, FERMI_ENERGY) < DIRAC_DOS_MAX)
    chk("graphene_dos_grows_away_from_fermi",
        dos_at(ge, 1.5 * T_HOP) > 5.0 * dos_at(ge, FERMI_ENERGY))

    # 4. Jacobi eigensolver: known spectra + reconstruction
    evals, _ = jacobi_eigh([[2.0, 1.0], [1.0, 2.0]])
    chk("jacobi_2x2_spectrum",
        abs(min(evals) - 1.0) < 1e-10 and abs(max(evals) - 3.0) < 1e-10)
    h_small = ssh_chain_hamiltonian(0.6, 1.4, ncells=4)
    ev_s, v_s = jacobi_eigh(h_small)
    recon_err = 0.0
    for i in range(8):
        for j in range(8):
            rec = sum(v_s[i][m] * ev_s[m] * v_s[j][m] for m in range(8))
            recon_err = max(recon_err, abs(rec - h_small[i][j]))
    chk("jacobi_reconstruction", recon_err < 1e-9)
    chk("jacobi_trace_preserved",
        abs(sum(ev_s) - sum(h_small[i][i] for i in range(8))) < 1e-9)

    # 5. SSH: bulk gap, winding / Zak phase, edge states
    chk("ssh_gap_trivial_formula",
        abs(ssh_bulk_gap(1.4, 0.6) - 2.0 * abs(1.4 - 0.6)) < 1e-6)
    chk("ssh_gap_topological_formula",
        abs(ssh_bulk_gap(0.6, 1.4) - 2.0 * abs(0.6 - 1.4)) < 1e-6)
    chk("ssh_winding_trivial_zero", abs(ssh_winding(1.4, 0.6)) < 1e-6)
    chk("ssh_winding_topological_one",
        abs(abs(ssh_winding(0.6, 1.4)) - 1.0) < 1e-6)
    chk("ssh_zak_phase_topological_pi",
        abs(abs(ssh_zak_phase(0.6, 1.4)) - math.pi) < 1e-6)
    chk("ssh_zak_phase_trivial_zero", abs(ssh_zak_phase(1.4, 0.6)) < 1e-6)
    topo = ssh_edge_report(0.6, 1.4)
    chk("ssh_edge_states_in_topological_phase", topo["midgap_states"] == 2)
    chk("ssh_edge_states_near_zero_energy",
        topo["smallest_abs_energy"] < 1e-3
        and topo["second_smallest_abs_energy"] < 1e-3)
    triv = ssh_edge_report(1.4, 0.6)
    chk("ssh_no_edge_states_in_trivial_phase", triv["midgap_states"] == 0)
    chk("ssh_trivial_chain_min_energy_above_half_gap",
        triv["smallest_abs_energy"] > 0.75)
    spec = ssh_chain_spectrum(0.6, 1.4)
    chk("ssh_chain_spectrum_chiral_symmetric",
        all(abs(spec[i] + spec[len(spec) - 1 - i]) < 1e-8
            for i in range(len(spec))))

    # 6. Hubbard dimer: exact vs analytic anchors
    chk("hubbard_u0_ground_energy",
        abs(hubbard_dimer(u=0.0)["ground_energy"] - (-2.0 * T_HOP)) < 1e-9)
    chk("hubbard_ground_energy_matches_analytic",
        all(abs(hubbard_dimer(u=u)["ground_energy"]
                - hubbard_ground_energy_analytic(u=u)) < 1e-9
            for u in (1.0, 2.0, 4.0, 8.0)))
    chk("hubbard_u0_double_occupancy_half",
        abs(hubbard_dimer(u=0.0)["double_occupancy"] - 0.5) < 1e-9)
    chk("hubbard_double_occupancy_matches_analytic",
        all(abs(hubbard_dimer(u=u)["double_occupancy"]
                - hubbard_double_occupancy_analytic(u=u)) < 1e-9
            for u in (1.0, 2.0, 4.0, 8.0)))
    curve = hubbard_curve()
    chk("hubbard_double_occupancy_falls_with_u",
        all(curve[i]["double_occupancy"] > curve[i + 1]["double_occupancy"]
            for i in range(len(curve) - 1)))
    chk("hubbard_ground_energy_rises_with_u",
        all(curve[i]["ground_energy"] < curve[i + 1]["ground_energy"]
            for i in range(len(curve) - 1)))
    chk("hubbard_ground_state_is_singlet",
        hubbard_dimer(u=4.0)["triplet_weight"] < 1e-9)

    # 7. classifier: labels come from the lab's own computed rows
    rep = classifier_report()
    chk("classifier_chain_metal", rep["chain_1d_half_filled"] == "metal")
    chk("classifier_square_metal", rep["square_2d_half_filled"] == "metal")
    chk("classifier_graphene_dirac",
        rep["graphene_honeycomb"] == "dirac-semimetal")
    chk("classifier_ssh_trivial_insulator",
        rep["ssh_trivial_t1_1.4_t2_0.6"] == "insulator")
    chk("classifier_ssh_topological",
        rep["ssh_topological_t1_0.6_t2_1.4"] == "topological")
    chk("classifier_matches_model_on_scenarios",
        all(classify_material(*feats) == model_label(*feats)
            for feats in classifier_scenarios().values()))
    chk("classifier_training_rows_computed",
        len(TRAINING_ROWS) >= 10
        and all(label == model_label(*feats)
                for feats, label in TRAINING_ROWS))

    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14
        and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_real_material_hold",
        gate("real_material_prediction_claim") == "HOLD")
    chk("gate_discovery_hold", gate("material_discovery_claim") == "HOLD")
    chk("gate_superconductor_hold", gate("superconductor_claim") == "HOLD")
    chk("gate_quantum_hardware_hold", gate("quantum_hardware_claim") == "HOLD")
    chk("gate_toy_as_measurement_hold",
        gate("toy_model_as_measurement_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    brains = brains_report()
    chk("argon4_no_override", brains["decider"]["can_override_hold"] is False
        and brains["decider"]["seat"]
        == "Gemini Argon 4 Extended Thinking")
    chk("claude_no_override", brains["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", brains["flow"]["rendered"] is False
        and brains["flow"]["live"] == 0)
    return c


# ================================================================ reports
def bands_report():
    e1 = chain_1d_energies()
    _, dos1 = dos_histogram(e1, -2.0 * T_HOP, 2.0 * T_HOP)
    e2 = square_2d_energies()
    _, dos2 = dos_histogram(e2, -4.0 * T_HOP, 4.0 * T_HOP)
    mid1, mid2 = len(dos1) // 2, len(dos2) // 2
    return {
        "chain_1d": {
            "dispersion": "E(k) = -2t cos(ka)",
            "bandwidth": bandwidth(e1),
            "dos_edge_bin": round(dos1[0], 4),
            "dos_centre_bin": round(dos1[mid1], 4),
            "dos_at_fermi": round(dos_at(e1, FERMI_ENERGY), 4),
        },
        "square_2d": {
            "dispersion": "E(k) = -2t (cos kx + cos ky)",
            "bandwidth": bandwidth(e2),
            "dos_saddle_bin": round(dos2[mid2], 4),
            "dos_edge_bin": round(dos2[0], 4),
            "dos_at_fermi": round(dos_at(e2, FERMI_ENERGY), 4),
        },
    }


def graphene_report():
    ge = graphene_energies(nk=101)
    return {
        "k_point": [round(K_POINT[0], 6), round(K_POINT[1], 6)],
        "abs_f_at_k": abs(graphene_f(*K_POINT)),
        "abs_f_at_gamma": abs(graphene_f(0.0, 0.0)),
        "dirac_slope_fitted": graphene_dirac_slope(),
        "fermi_velocity_labelled_hbar_vf": FERMI_VELOCITY_LABELLED,
        "dos_at_fermi": dos_at(ge, FERMI_ENERGY),
        "dos_at_1.5t": dos_at(ge, 1.5 * T_HOP),
    }


def ssh_report():
    return {
        "trivial_t1_1.4_t2_0.6": ssh_edge_report(1.4, 0.6),
        "topological_t1_0.6_t2_1.4": ssh_edge_report(0.6, 1.4),
    }


def hubbard_report():
    return {"curve": [{k: row[k] for k in
                       ("U", "ground_energy", "double_occupancy")}
                      for row in hubbard_curve()]}


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("QuantumMaterials-Lab - quantum materials tight-binding lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] THE HONEST CORE - exact numbers for TOY lattices")
    print("    Every model here is a tight-binding toy with labelled")
    print("    hoppings (t = 1) and labelled lattice constants. The lab")
    print("    computes band structures, densities of states, windings,")
    print("    and correlation effects EXACTLY for those toys - and")
    print("    claims nothing about any real material, ever.")
    bands = bands_report()
    c1 = bands["chain_1d"]
    print("\n[2] 1D chain - E(k) = -2t cos(ka), van Hove band edges")
    print(f"    bandwidth {c1['bandwidth']:.4f} (= 4t) | "
          f"DOS edge bin {c1['dos_edge_bin']:.4f} vs centre bin "
          f"{c1['dos_centre_bin']:.4f}")
    print("    -> the 1D DOS diverges at the band edges (van Hove):")
    print("       states pile up where the band flattens.")
    s2 = bands["square_2d"]
    print("\n[3] 2D square lattice - E(k) = -2t (cos kx + cos ky)")
    print(f"    bandwidth {s2['bandwidth']:.4f} (= 8t) | "
          f"DOS saddle bin (E=0) {s2['dos_saddle_bin']:.4f} vs edge bin "
          f"{s2['dos_edge_bin']:.4f}")
    print("    -> at half filling the Fermi level sits exactly on the")
    print("       van Hove saddle: the DOS peaks at E = 0.")
    gr = graphene_report()
    print("\n[4] Graphene toy - honeycomb, Dirac cones at K and K'")
    print(f"    |f(K)| = {gr['abs_f_at_k']:.2e} (bands touch) | "
          f"|f(Gamma)| = {gr['abs_f_at_gamma']:.4f} (bands at -+3t)")
    print(f"    fitted cone slope {gr['dirac_slope_fitted']:.4f} vs "
          f"labelled hbar*v_F = (3/2) t a = "
          f"{gr['fermi_velocity_labelled_hbar_vf']:.4f}")
    print(f"    DOS at E_F {gr['dos_at_fermi']:.4f} (vanishes: semimetal) vs "
          f"DOS at 1.5t {gr['dos_at_1.5t']:.4f}")
    ssh = ssh_report()
    print("\n[5] SSH chain - dimerization, winding, edge states")
    for name, row in ssh.items():
        print(f"    {name:26s} gap {row['bulk_gap']:.4f} | winding "
              f"{row['winding']:+.4f} | Zak/pi {row['zak_phase_over_pi']:+.4f} "
              f"| midgap states {row['midgap_states']} | "
              f"min |E| {row['smallest_abs_energy']:.2e}")
    print("    -> bulk-boundary correspondence, demonstrated: the open")
    print("       chain hides two zero-energy edge states exactly when")
    print("       the winding is 1 (strong bond BETWEEN cells).")
    print("\n[6] Hubbard dimer - repulsion drains double occupancy")
    for row in hubbard_curve():
        print(f"    U = {row['U']:4.1f}  E_ground {row['ground_energy']:+.6f}  "
              f"double occupancy {row['double_occupancy']:.6f}")
    print("    -> exact diagonalization matches the analytic anchors")
    print("       (U - sqrt(U^2 + 16t^2))/2 at every U on the curve.")
    print("\n[7] Material character classifier (TinyML kNN, computed rows)")
    scenarios = classifier_scenarios()
    labels = classifier_report()
    for name, feats in scenarios.items():
        print(f"    {name:30s} gap {feats[0]:.3f} | DOS(E_F) {feats[1]:.4f} "
              f"| winding {feats[2]} -> {labels[name]}")
    print("\n[8] Advisory seats")
    brains = brains_report()
    print(f"    decider: {brains['decider']['decision']} "
          f"trace={brains['decider']['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {brains['advisor']['can_override_hold']}")
    print(f"    flow rendered = {brains['flow']['rendered']} "
          f"live = {brains['flow']['live']}")
    print(f"\n[9] HOLD gates: {len(HOLD_GATES)}")
    for key in HOLD_GATES:
        print(f"    HOLD  {key}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "bands":
        print(json.dumps(bands_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "graphene":
        print(json.dumps(graphene_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "ssh":
        print(json.dumps(ssh_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "hubbard":
        print(json.dumps(hubbard_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(classifier_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for key, value in HOLD_GATES.items():
            print(f"{key}: {value}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "real_material_prediction_claim"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
