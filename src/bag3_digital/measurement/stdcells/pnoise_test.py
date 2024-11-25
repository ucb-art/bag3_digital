from typing import Any, Mapping, Optional, Sequence
from pathlib import Path
import numpy as np

from bag.simulation.cache import SimulationDB, DesignInstance
from bag.simulation.measure import MeasurementManager
from bag.simulation.data import SimData
from bag.concurrent.util import GatherHelper

from bag3_testbenches.measurement.pnoise.base import PNoiseTB
from bag3_testbenches.measurement.digital.util import setup_digital_tran


class PNoiseTestMeas(MeasurementManager):
    async def async_measure_performance(self, name: str, sim_dir: Path, sim_db: SimulationDB,
                                        dut: Optional[DesignInstance],
                                        harnesses: Optional[Sequence[DesignInstance]] = None) -> Mapping[str, Any]:
        helper = GatherHelper()
        sim_envs = self.specs['sim_envs']
        for sim_env in sim_envs:
            helper.append(self.async_meas_case(name, sim_dir / sim_env, sim_db, dut, harnesses, sim_env))

        meas_results = await helper.gather_err()
        results = {'sim_envs': np.array(sim_envs)}
        len_sim_envs = len(sim_envs)
        for key, val in meas_results[0].items():
            results[key] = np.zeros((len_sim_envs, *val.shape), dtype=float)

        for sidx, _ in enumerate(sim_envs):
            for key, val in meas_results[sidx].items():
                results[key][sidx] = val

        return results

    async def async_meas_case(self, name: str, sim_dir: Path, sim_db: SimulationDB, dut: Optional[DesignInstance],
                              harnesses: Optional[Sequence[DesignInstance]], sim_env: str) -> Mapping[str, Any]:
        load_list = [dict(type='vpulse', lib='analogLib', conns=dict(PLUS='in', MINUS='VSS'),
                          value={'v1': 'v_VSS', 'v2': 'v_VDD', 'per': 't_per', 'pw': 't_per/2',
                                 'tr': 't_rf', 'tf': 't_rf', 'td': 't_delay'})]
        tb_params = dict(
            # pin_values={'outb': 'in'},
            sim_envs=[sim_env],
            load_list=load_list,
        )
        tbm_specs, tb_params = setup_digital_tran(self.specs, dut, **tb_params)
        tbm = self.make_tbm(PNoiseTB, tbm_specs)

        sim_results = await sim_db.async_simulate_tbm_obj(name, sim_dir, dut, tbm, tb_params, harnesses=harnesses)
        results = self.process_data(sim_results.data)
        return results

    @staticmethod
    def process_data(sim_data: SimData) -> Mapping[str, Any]:
        # TODO
        breakpoint()
        return {}
