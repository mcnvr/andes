import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from andes.system import System


def numpy_to_python(obj: Any) -> Any:
    """
    Convert numpy types to Python native types for JSON serialization.

    Parameters
    ----------
    obj : Any
        Object to convert (may be numpy array, scalar, or other type)

    Returns
    -------
    Any
        Python native type
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [numpy_to_python(item) for item in obj]
    return obj


def serialize_system_info(system: System) -> dict:
    """
    Serialize basic system information.

    Parameters
    ----------
    system : System
        ANDES System object

    Returns
    -------
    dict
        System information including model counts, configuration, etc.
    """
    info = {
        "name": system.name or "Untitled",
        "case_path": str(system.files.case) if system.files.case else None,
        "is_setup": system.is_setup,
        "models": {},
        "dae_info": {
            "n_states": int(system.dae.n),
            "n_algebraic": int(system.dae.m),
            "time": float(system.dae.t) if hasattr(system.dae, 't') else 0.0,
        },
        "config": {
            "freq": float(system.config.freq),
            "mva": float(system.config.mva),
        },
    }

    # Add model counts
    for name, model in system.models.items():
        if model.n > 0:
            info["models"][name] = {
                "count": int(model.n),
                "group": model.group,
            }

    return info


def serialize_pflow_results(system: System) -> dict:
    """
    Serialize power flow results.

    Parameters
    ----------
    system : System
        ANDES System object with completed power flow

    Returns
    -------
    dict
        Power flow results including bus voltages, angles, and convergence info
    """
    if not system.PFlow.converged:
        return {
            "converged": False,
            "iterations": system.PFlow.niter,
            "error": "Power flow did not converge"
        }

    results = {
        "converged": True,
        "iterations": system.PFlow.niter,
        "exec_time": float(system.PFlow.exec_time),
        "buses": {},
        "summary": {},
    }

    # Bus results
    if hasattr(system, 'Bus') and system.Bus.n > 0:
        results["buses"] = {
            "idx": numpy_to_python(system.Bus.idx.v),
            "name": [str(n) for n in system.Bus.name.v] if hasattr(system.Bus, 'name') else [],
            "voltage": numpy_to_python(system.Bus.v.v),
            "angle": numpy_to_python(system.Bus.a.v),
        }

    # Generator results if available
    # StaticGen is a group, so we need to collect from individual generator models
    gen_idx = []
    gen_p = []
    gen_q = []

    for model_name in ['Slack', 'PV', 'PQ']:
        if hasattr(system, model_name):
            model = getattr(system, model_name)
            if hasattr(model, 'n') and model.n > 0:
                if hasattr(model, 'idx') and hasattr(model.idx, 'v'):
                    gen_idx.extend(numpy_to_python(model.idx.v))
                if hasattr(model, 'p') and hasattr(model.p, 'v'):
                    gen_p.extend(numpy_to_python(model.p.v))
                if hasattr(model, 'q') and hasattr(model.q, 'v'):
                    gen_q.extend(numpy_to_python(model.q.v))

    if gen_idx:
        results["generators"] = {
            "idx": gen_idx,
            "p": gen_p,
            "q": gen_q,
        }

    return results


def serialize_tds_results(
    system: System,
    variables: Optional[List[str]] = None,
    max_points: Optional[int] = None
) -> dict:
    """
    Serialize time-domain simulation results.

    Parameters
    ----------
    system : System
        ANDES System object with completed TDS
    variables : Optional[List[str]]
        Specific variable names to return. If None, returns all.
    max_points : Optional[int]
        Maximum number of data points to return (downsampling if needed)

    Returns
    -------
    dict
        Time-domain results including time series data
    """
    if not system.TDS.initialized:
        return {
            "initialized": False,
            "error": "Time-domain simulation not initialized"
        }

    dae = system.dae

    # Get time array
    time_array = numpy_to_python(dae.ts.t)

    results = {
        "initialized": True,
        "converged": not system.TDS.busted,
        "exec_time": float(system.TDS.exec_time) if hasattr(system.TDS, 'exec_time') else None,
        "time": time_array,
        "n_points": len(time_array),
        "variables": {},
    }

    # Determine which variables to include
    if variables is None:
        # Include all state variables
        var_names = dae.x_name
        var_data = dae.ts.x
    else:
        # Filter requested variables
        var_names = []
        var_data = []
        for var_name in variables:
            if var_name in dae.x_name:
                idx = dae.x_name.index(var_name)
                var_names.append(var_name)
                var_data.append(dae.ts.x[:, idx])
            elif var_name in dae.y_name:
                idx = dae.y_name.index(var_name)
                var_names.append(var_name)
                var_data.append(dae.ts.y[:, idx])

    # Apply downsampling if needed
    if max_points and len(time_array) > max_points:
        step = len(time_array) // max_points
        results["time"] = time_array[::step]
        results["downsampled"] = True
        results["downsample_factor"] = step
    else:
        results["downsampled"] = False

    # Add variable data
    for i, name in enumerate(var_names):
        if isinstance(var_data, list):
            data = var_data[i]
        else:
            data = var_data[:, i] if len(var_data.shape) > 1 else var_data

        if results.get("downsampled"):
            data = data[::results["downsample_factor"]]

        results["variables"][name] = numpy_to_python(data)

    return results


def serialize_eig_results(system: System) -> dict:
    """
    Serialize eigenvalue analysis results.

    Parameters
    ----------
    system : System
        ANDES System object with completed eigenvalue analysis

    Returns
    -------
    dict
        Eigenvalue analysis results
    """
    if not hasattr(system, 'EIG'):
        return {
            "success": False,
            "error": "Eigenvalue analysis module not available"
        }

    eig = system.EIG

    # Check if eigenvalue analysis has been run (mu will be populated after run())
    if eig.mu is None:
        return {
            "success": False,
            "error": "Eigenvalue analysis has not been run yet"
        }

    results = {
        "n_eigenvalues": len(eig.mu),
        "eigenvalues": {
            "real": numpy_to_python(np.real(eig.mu)),
            "imag": numpy_to_python(np.imag(eig.mu)),
        },
        "statistics": {
            "n_positive": int(eig.n_positive),
            "n_zeros": int(eig.n_zeros),
            "n_negative": int(eig.n_negative),
        },
    }

    # Add participation factors if available
    if eig.pfactors is not None:
        results["participation_factors"] = numpy_to_python(eig.pfactors)

    # Add state names if available
    if eig.x_name is not None and len(eig.x_name) > 0:
        results["state_names"] = [str(name) for name in eig.x_name]

    # Add execution time if available
    if hasattr(eig, 'exec_time'):
        results["exec_time"] = float(eig.exec_time)

    return results
