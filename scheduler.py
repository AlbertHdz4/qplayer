import database
import hardware
import sequence

import random


class Scheduler:

    def __init__(self, seq: sequence.Sequence, hw: hardware.Hardware, db: database.Database):
        self.sequence = seq
        self.hardware = hw
        self.database = db
        self.hardware.add_sequence_end_listener(self.sequence_finished)

        # TODO: run_id and iter_id should be loaded and saved into a database
        self.run_id = 0
        self.iter_id = 0

        self.run_idx = 0 # used for iterations
        self.iter_indices = None

        self.continuous = False
        self.advance_indices = False
        self.shuffle = False

    def play_once(self):
        print("Run single")
        self.hardware.cycle_init()
        self.play()

    # Utility method called every time a sequence is executed.
    def play(self):
        csequence = self.sequence.playlist.compile_active_playlist()
        vars_dict = self.sequence.variables.get_variables_dict()
        self.hardware.process_sequence(csequence, self.run_id)
        self.hardware.play_once(self.run_id)
        self.database.store_run_parameters(self.run_id, vars_dict)
        self.run_id += 1


    def play_continuous(self):
        print("Run continuous")
        self.continuous = True
        self.hardware.cycle_init()
        self.play()

    def iterate(self):
        print("Iterate")
        iter_vars_dict = self.sequence.variables.get_iterating_variables()

        by_nesting_level = {}
        for var_name in iter_vars_dict:
            nesting_level = iter_vars_dict[var_name]['nesting level']
            num_values = iter_vars_dict[var_name]['num_values']
            by_nesting_level[nesting_level] = {'var_name' : var_name, 'num_values' : num_values}

        levels = list(by_nesting_level.keys())
        levels.sort()

        # Generate all indices
        self.iter_indices = []
        for level in levels:
            num_values = by_nesting_level[level]['num_values']
            var_name = by_nesting_level[level]['var_name']
            if level == 0:
                for i in range(num_values):
                    self.iter_indices.append({var_name:i})
            else:
                new_index_list = []
                for index_dict in self.iter_indices:
                    for i in range(num_values):
                        index_dict[var_name] = i
                        new_index_list.append(index_dict.copy())
                self.iter_indices = new_index_list

        if self.shuffle:
            random.shuffle(self.iter_indices)

        self.continuous = True
        self.advance_indices = True
        self.run_idx = 0
        self.sequence.variables.reset_indices()
        self.hardware.cycle_init()
        self.play()

    def stop(self):
        self.continuous = False
        self.advance_indices = False
        self.hardware.stop()

    def shuffle_on(self):
        self.shuffle = True

    def shuffle_off(self):
        self.shuffle = False

    # This function is called when the hardware is ready to receive the next new sequence
    def sequence_finished(self):
        print("scheduler: Ready for next one")
        if self.advance_indices:
            self.run_idx += 1
            if self.run_idx == len(self.iter_indices):
                self.iter_id += 1
                self.run_idx = 0
                if self.shuffle:
                    random.shuffle(self.iter_indices)
            next_indices = self.iter_indices[self.run_idx]
            print(next_indices)
            self.sequence.variables.set_iterating_variables_indices(next_indices)

        if self.continuous:
            self.play()
