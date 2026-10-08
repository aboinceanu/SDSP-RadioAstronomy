import numpy as np
import scipy
import scipy as sp
import scipy.io
from scipy.ndimage import gaussian_filter
c = 3e8
class Processor:
    def __init__(self):
        self.covariance_matrix = None
        self.covariance_matrix_inv = None
        self.cov_mat_inv_sq = None
        self.antenna_positions = None
        self.frequency = None
        self.steering_matrix = None
        self.sky_mask = None
        self.grid_shape = None
        self.resolution = 150
        self.clean_iterations = 20
        self.clean_loopgain = 0.1

    def load_dataset(self, file_path):

        mat_data = scipy.io.loadmat(file_path)
        self.covariance_matrix = mat_data['Rh']
        self.antenna_positions = mat_data['poslocal']
        self.frequency = mat_data['freq']
        self.covariance_matrix_inv = np.linalg.inv(self.covariance_matrix)
        self.cov_mat_inv_sq = self.covariance_matrix_inv @ self.covariance_matrix_inv
        return list(mat_data.keys())

    def update_clean_parameters(self, new_iterations, new_loopgain):
        if self.clean_iterations != new_iterations:
            self.clean_iterations = new_iterations
            self.steering_matrix = None
            self.sky_mask = None
            self.grid_shape = None

        if self.clean_loopgain != new_loopgain:
            self.clean_loopgain = new_loopgain
            self.steering_matrix = None
            self.sky_mask = None
            self.grid_shape = None

    def update_res(self, new_resolution):
        if self.resolution != new_resolution:
            self.resolution = new_resolution
            self.steering_matrix = None
            self.sky_mask = None
            self.grid_shape = None

    def steering_matrix_gen(self):
        nm, nl = (self.resolution, self.resolution)
        m = np.linspace(-1,1, nm)
        l = np.linspace(-1,1, nl)
        mesh_m, mesh_l = np.meshgrid(m, l)
        mesh_n = np.sqrt(np.maximum(0, 1 - mesh_l**2 - mesh_m**2))
        self.sky_mask = (mesh_l**2 + mesh_m**2) <= 1
        valid_l = mesh_l[self.sky_mask]
        valid_m = mesh_m[self.sky_mask]
        valid_n = mesh_n[self.sky_mask]
        source_pos_vec = np.vstack((valid_l, valid_m, valid_n))

        phase_delay = ((2*np.pi*self.frequency/c)*self.antenna_positions)@source_pos_vec
        self.steering_matrix = np.exp(-1j*phase_delay)
        self.grid_shape = mesh_l.shape



    def compute_image(self, algorithm = "matched"):
        image = None
        if not hasattr(self, "steering_matrix") or self.steering_matrix is None:
            self.steering_matrix_gen()

        if algorithm == "matched":
            intensities = np.sum(self.steering_matrix.conj() * (self.covariance_matrix @ self.steering_matrix), axis=0).real
            image = np.full(self.grid_shape, np.nan)
            image[self.sky_mask] = intensities
            image[~self.sky_mask] = np.nan

        if algorithm == "mvdr":
            denom = np.sum(self.steering_matrix.conj() * (self.covariance_matrix_inv @ self.steering_matrix), axis=0).real
            intensities = 1/(denom + 1e-12)
            image = np.full(self.grid_shape, np.nan)
            image[self.sky_mask] = intensities
            image[~self.sky_mask] = np.nan

        if algorithm == "clean":
            J = self.antenna_positions.shape[0]
            clean_intensities = np.zeros(self.steering_matrix.shape[1])
            dirty_intensities = np.sum(self.steering_matrix.conj() * (self.covariance_matrix @ self.steering_matrix), axis=0).real

            for _ in range(self.clean_iterations):
                peak_idx = np.argmax(dirty_intensities)
                peak_power = dirty_intensities[peak_idx] / (J ** 2)
                if peak_power <= 0:
                    break
                clean_intensities[peak_idx] += peak_power * self.clean_loopgain
                c_vec = self.steering_matrix.conj().T @ self.steering_matrix[:, peak_idx]
                c_vec_sq = c_vec.real**2 + c_vec.imag**2
                dirty_intensities -= peak_power* self.clean_loopgain * c_vec_sq

            cleaned_image = np.full(self.grid_shape, 0.0)
            cleaned_image[self.sky_mask] = clean_intensities

            synth_beam_sigma = 1
            impulse = np.zeros(self.grid_shape)
            impulse[self.grid_shape[0] // 2, self.grid_shape[1] // 2] = 1.0
            peak = gaussian_filter(impulse, sigma=synth_beam_sigma).max()
            syth_smooth = gaussian_filter(cleaned_image, sigma=synth_beam_sigma) / peak

            res_dirty_image = np.full(self.grid_shape, np.nan)
            res_dirty_image[self.sky_mask] = dirty_intensities

            image = syth_smooth + res_dirty_image/(J**2)
            image[~self.sky_mask] = np.nan
            return image

        if algorithm == "aar":
            num = np.sum(self.steering_matrix.conj() * (self.covariance_matrix_inv @ self.steering_matrix), axis=0).real
            denom = np.sum(self.steering_matrix.conj() * (self.cov_mat_inv_sq @ self.steering_matrix), axis=0).real ** 2
            intensities = num/(denom + 1e-12)
            image = np.full(self.grid_shape, np.nan)
            image[self.sky_mask] = intensities
            image[~self.sky_mask] = np.nan            

        return image