"""Tests for QuantumMaterials-Lab: tight-binding bands, DOS van Hove
structure, graphene Dirac cones, SSH topology + edge states, Hubbard
dimer exactness, classifier, gates, determinism."""
import math
import subprocess
import sys
from pathlib import Path

import main as m

ROOT = Path(__file__).resolve().parent.parent


# ---- 1D chain
def test_chain_bandwidth():
    assert abs(m.bandwidth(m.chain_1d_energies()) - 4.0) < 1e-9


def test_chain_endpoints():
    assert m.chain_1d_energy(0.0) == -2.0
    assert abs(m.chain_1d_energy(math.pi) - 2.0) < 1e-12


def test_chain_dos_van_hove():
    _, dos = m.dos_histogram(m.chain_1d_energies(), -2.0, 2.0)
    mid = len(dos) // 2
    assert dos[0] > dos[mid] and dos[-1] > dos[mid]


def test_chain_dos_at_fermi():
    assert m.dos_at(m.chain_1d_energies(), 0.0) > 0.1


# ---- 2D square lattice
def test_square_bandwidth():
    assert abs(m.bandwidth(m.square_2d_energies()) - 8.0) < 1e-9


def test_square_high_symmetry():
    assert m.square_2d_energy(0.0, 0.0) == -4.0
    assert abs(m.square_2d_energy(math.pi, math.pi) - 4.0) < 1e-12
    assert abs(m.square_2d_energy(math.pi, 0.0)) < 1e-12


def test_square_dos_saddle_peak():
    _, dos = m.dos_histogram(m.square_2d_energies(), -4.0, 4.0)
    mid = len(dos) // 2
    assert dos[mid] == max(dos)
    assert dos[mid] > dos[0] and dos[mid] > dos[-1]


# ---- graphene toy
def test_graphene_dirac_points():
    assert abs(m.graphene_f(*m.K_POINT)) < 1e-9
    assert abs(m.graphene_f(*m.K_PRIME)) < 1e-9
    lo, hi = m.graphene_bands(*m.K_POINT)
    assert abs(lo) < 1e-9 and abs(hi) < 1e-9


def test_graphene_gamma():
    assert abs(abs(m.graphene_f(0.0, 0.0)) - 3.0) < 1e-12
    assert m.graphene_bands(0.0, 0.0) == (-3.0, 3.0)


def test_graphene_dirac_slope():
    slope = m.graphene_dirac_slope()
    assert abs(slope - 1.5) < 0.05 * 1.5
    assert m.FERMI_VELOCITY_LABELLED == 1.5 * m.T_HOP * m.A_CC


def test_graphene_dos_vanishes_at_fermi():
    energies = m.graphene_energies(nk=101)
    assert m.dos_at(energies, 0.0) < m.DIRAC_DOS_MAX
    assert m.dos_at(energies, 1.5) > 5.0 * m.dos_at(energies, 0.0)


# ---- Jacobi eigensolver
def test_jacobi_known_spectra():
    evals, _ = m.jacobi_eigh([[2.0, 1.0], [1.0, 2.0]])
    assert abs(min(evals) - 1.0) < 1e-10
    assert abs(max(evals) - 3.0) < 1e-10
    evals, _ = m.jacobi_eigh([[1.0, 0.0], [0.0, -5.0]])
    assert sorted(evals) == [-5.0, 1.0]


def test_jacobi_reconstruction():
    h = m.ssh_chain_hamiltonian(0.6, 1.4, ncells=4)
    evals, vecs = m.jacobi_eigh(h)
    for i in range(8):
        for j in range(8):
            rec = sum(vecs[i][k] * evals[k] * vecs[j][k] for k in range(8))
            assert abs(rec - h[i][j]) < 1e-9


# ---- SSH chain
def test_ssh_bulk_gap_formula():
    assert abs(m.ssh_bulk_gap(1.4, 0.6) - 1.6) < 1e-6
    assert abs(m.ssh_bulk_gap(0.6, 1.4) - 1.6) < 1e-6
    assert abs(m.ssh_bulk_gap(1.0, 1.0)) < 1e-6


def test_ssh_winding_and_zak():
    assert abs(m.ssh_winding(1.4, 0.6)) < 1e-6
    assert abs(abs(m.ssh_winding(0.6, 1.4)) - 1.0) < 1e-6
    assert abs(m.ssh_zak_phase(1.4, 0.6)) < 1e-6
    assert abs(abs(m.ssh_zak_phase(0.6, 1.4)) - math.pi) < 1e-6


def test_ssh_edge_states_topological():
    report = m.ssh_edge_report(0.6, 1.4)
    assert report["midgap_states"] == 2
    assert report["smallest_abs_energy"] < 1e-3
    assert report["second_smallest_abs_energy"] < 1e-3


def test_ssh_no_edge_states_trivial():
    report = m.ssh_edge_report(1.4, 0.6)
    assert report["midgap_states"] == 0
    assert report["smallest_abs_energy"] > 0.75


def test_ssh_chain_chiral_symmetry():
    spec = m.ssh_chain_spectrum(0.6, 1.4)
    n = len(spec)
    assert all(abs(spec[i] + spec[n - 1 - i]) < 1e-8 for i in range(n))


# ---- Hubbard dimer
def test_hubbard_u0():
    row = m.hubbard_dimer(u=0.0)
    assert abs(row["ground_energy"] - (-2.0)) < 1e-9
    assert abs(row["double_occupancy"] - 0.5) < 1e-9


def test_hubbard_matches_analytic():
    for u in (1.0, 2.0, 4.0, 8.0):
        row = m.hubbard_dimer(u=u)
        assert abs(row["ground_energy"]
                   - m.hubbard_ground_energy_analytic(u=u)) < 1e-9
        assert abs(row["double_occupancy"]
                   - m.hubbard_double_occupancy_analytic(u=u)) < 1e-9


def test_hubbard_double_occupancy_falls():
    curve = m.hubbard_curve()
    occ = [row["double_occupancy"] for row in curve]
    assert all(occ[i] > occ[i + 1] for i in range(len(occ) - 1))
    assert occ[-1] < 0.06


def test_hubbard_ground_state_singlet():
    assert m.hubbard_dimer(u=4.0)["triplet_weight"] < 1e-9


# ---- classifier
def test_classifier_scenarios():
    rep = m.classifier_report()
    assert rep["chain_1d_half_filled"] == "metal"
    assert rep["square_2d_half_filled"] == "metal"
    assert rep["graphene_honeycomb"] == "dirac-semimetal"
    assert rep["ssh_trivial_t1_1.4_t2_0.6"] == "insulator"
    assert rep["ssh_topological_t1_0.6_t2_1.4"] == "topological"


def test_classifier_matches_model():
    for feats in m.classifier_scenarios().values():
        assert m.classify_material(*feats) == m.model_label(*feats)
    for feats, label in m.TRAINING_ROWS:
        assert label == m.model_label(*feats)


def test_model_label_policy():
    assert m.model_label(1.6, 0.0, 1) == "topological"
    assert m.model_label(1.6, 0.0, 0) == "insulator"
    assert m.model_label(0.0, 0.01, 0) == "dirac-semimetal"
    assert m.model_label(0.0, 0.30, 0) == "metal"


# ---- gates + seats
def test_hold_gates():
    assert len(m.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())
    assert m.gate("real_material_prediction_claim") == "HOLD"
    assert m.gate("superconductor_claim") == "HOLD"
    assert m.gate("toy_model_as_measurement_claim") == "HOLD"
    assert m.gate("run_simulation") == "PROCEED"


def test_council_seats():
    brains = m.brains_report()
    assert brains["decider"]["seat"] == "Gemini Argon 4 Extended Thinking"
    assert brains["decider"]["can_override_hold"] is False
    assert brains["advisor"]["can_override_hold"] is False
    assert brains["flow"]["rendered"] is False
    assert brains["flow"]["live"] == 0


# ---- checks suite + CLI behaviour
def test_run_checks_all_pass():
    checks = m.run_checks()
    assert all(ok for _, ok in checks), [n for n, ok in checks if not ok]
    assert len(checks) == 59


def test_cli_checks_and_holds():
    out = subprocess.run([sys.executable, "main.py", "checks"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0
    assert "CHECKS 59/59" in out.stdout
    out = subprocess.run([sys.executable, "main.py", "holds"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0
    assert "toy_model_as_measurement_claim" in out.stdout


def test_cli_hold_demo_exits_2():
    out = subprocess.run([sys.executable, "main.py", "hold-demo"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 2
    out = subprocess.run([sys.executable, "main.py", "hold-demo",
                          "material_discovery_claim"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 2


def test_demo_deterministic():
    runs = []
    for _ in range(2):
        out = subprocess.run([sys.executable, "main.py", "demo"],
                             cwd=ROOT, capture_output=True, text=True)
        assert out.returncode == 0
        runs.append(out.stdout)
    assert runs[0] == runs[1]
    assert "CHECKS 59/59" in runs[0]
