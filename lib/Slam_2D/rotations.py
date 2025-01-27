# Utility file with functions for handling rotations
#
# Author: Trevor Ablett
# University of Toronto Institute for Aerospace Studies

import numpy as np

def skew_symmetric(v):
    """ Skew symmetric operator for a 3x1 vector. """
    
    v = np.asarray(v).flatten()  # Ensure `v` is a 1D array
    if v.shape[0] != 3:
        raise ValueError("Input vector must be a 1D array with exactly 3 elements.")
    
    return np.array(
        [[0, -v[2], v[1]],
         [v[2], 0, -v[0]],
         [-v[1], v[0], 0]]
    )

class Quaternion():
    def __init__(self, w=1., x=0., y=0., z=0., axis_angle=None, euler=None):
        """
        Allow initialization either with explicit wxyz, axis angle, or euler XYZ (RPY) angles.

        :param w: w (real) of a quaternion.
        :param x: x (i) of a quaternion.
        :param y: y (j) of a quaternion.
        :param z: z (k) of a quaternion.
        :param axis_angle: Set of three values from axis-angle representation, as list or [3,] or [3,1] np.ndarray.
                           See C2M5L2 Slide 7 for details.
        :param euler: Set of three angles from euler XYZ rotating frame angles.
        """
        if axis_angle is None and euler is None:
            self.w = w
            self.x = x
            self.y = y
            self.z = z
        elif euler is not None and axis_angle is not None:
            raise AttributeError("Only one of axis_angle and euler can be specified.")
        elif axis_angle is not None:
            if not (type(axis_angle) == list or type(axis_angle) == np.ndarray) or len(axis_angle) != 3:
                raise ValueError("axis_angle must be list or np.ndarray with length 3.")
            axis_angle = np.array(axis_angle)
            norm = np.linalg.norm(axis_angle)
            self.w = np.cos(norm / 2)
            if norm < 1e-50:  # to avoid instabilities and nans
                self.x = 0
                self.y = 0
                self.z = 0
            else:
                imag = axis_angle / norm * np.sin(norm / 2)
                self.x = imag[0].item()
                self.y = imag[1].item()
                self.z = imag[2].item()
        else:
            roll = euler[0]
            pitch = euler[1]
            yaw = euler[2]

            cy = np.cos(yaw * 0.5)
            sy = np.sin(yaw * 0.5)
            cr = np.cos(roll * 0.5)
            sr = np.sin(roll * 0.5)
            cp = np.cos(pitch * 0.5)
            sp = np.sin(pitch * 0.5)

            # static frame
            self.w = cr * cp * cy + sr * sp * sy
            self.x = sr * cp * cy - cr * sp * sy
            self.y = cr * sp * cy + sr * cp * sy
            self.z = cr * cp * sy - sr * sp * cy

            # rotating frame
            # self.w = cr * cp * cy - sr * sp * sy
            # self.x = cr * sp * sy + sr * cp * cy
            # self.y = cr * sp * cy - sr * cp * sy
            # self.z = cr * cp * sy + sr * sp * cy
    
    def to_numpy(self):
        """ Return numpy wxyz representation. """
        return np.array([self.w, self.x, self.y, self.z])

            
    def __mul__(self, other):
        if isinstance(other, (float, int)):  # Skalowanie kwaternionu przez liczbę
            return Quaternion(self.w * other, self.x * other, self.y * other, self.z * other)
        elif isinstance(other, Quaternion):  # Mnożenie dwóch kwaternionów
            return self.quat_mult(other, out='Quaternion')
        else:
            raise TypeError(f"Unsupported operand type(s) for *: 'Quaternion' and '{type(other).__name__}'")
        
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __add__(self, other):
        if isinstance(other, Quaternion):
            return Quaternion(
                self.w + other.w,
                self.x + other.x,
                self.y + other.y,
                self.z + other.z
            )
        else:
            raise TypeError(f"Unsupported operand type(s) for +: 'Quaternion' and '{type(other).__name__}'")


    def __repr__(self):
        return "Quaternion (wxyz): [%2.5f, %2.5f, %2.5f, %2.5f]" % (self.w, self.x, self.y, self.z)

    def to_mat(self):
        v = np.array([self.x, self.y, self.z]).reshape(3,1)
        v_1d = v.flatten()  # Convert to 1D for skew_symmetric
        return (self.w ** 2 - np.dot(v.T, v)) * np.eye(3) + \
               2 * np.dot(v, v.T) + 2 * self.w * skew_symmetric(v_1d)

    def to_euler(self):
        """ Return as xyz (roll pitch yaw) Euler angles, with a static frame """
        roll = np.arctan2(2 * (self.w * self.x + self.y * self.z), 1 - 2 * (self.x**2 + self.y**2))
        pitch = np.arcsin(2 * (self.w * self.y - self.z * self.x))
        yaw = np.arctan2(2 * (self.w * self.z + self.x * self.y), 1 - 2 * (self.y**2 + self.z**2))
        return np.array([roll, pitch, yaw])

    def to_numpy(self):
        """ Return numpy wxyz representation. """
        return np.array([self.w, self.x, self.y, self.z])

    def normalize(self):
        """ Return a normalized version of this quaternion to ensure that it is valid. """
        norm = np.linalg.norm([self.w, self.x, self.y, self.z])
        return Quaternion(self.w / norm, self.x / norm, self.y / norm, self.z / norm)

    def quat_mult(self, q, out='np'):
        """
        Give output of multiplying this quaternion by another quaternion.
        See equation from C2M5L2 Slide 7 for details.

        :param q: The quaternion to multiply by, either a Quaternion or 4x1 ndarray.
        :param out: Output type, either np or Quaternion.
        :return: Returns quaternion of desired type
        """

        v = np.array([self.x, self.y, self.z]).reshape(3, 1)
        sum_term = np.zeros([4,4])
        sum_term[0,1:] = -v[:,0]
        sum_term[1:, 0] = v[:,0]
        sum_term[1:, 1:] = -skew_symmetric(v)
        sigma = self.w * np.eye(4) + sum_term

        if type(q).__name__ == "Quaternion":
            quat_np = np.dot(sigma, q.to_numpy())
        else:
            quat_np = np.dot(sigma, q)

        if out == 'np':
            return quat_np
        elif out == 'Quaternion':
            quat_obj = Quaternion(quat_np[0], quat_np[1], quat_np[2], quat_np[3])
            return quat_obj
