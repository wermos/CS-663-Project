import numpy as np
from scipy.spatial.distance import cdist

import constants
from data_loader import coil_20_data_loader, coil_100_data_loader
from train import train_model
from util import normalize, cubic_splines_to_vector

def evaluate_cubic_splines_for_angles(manifolds_universal, manifolds_object, angle_values):
    manifold_points_universal = np.array([cubic_splines_to_vector(manifolds_universal[object_id], angle_values) for object_id in range(constants.NUM_OBJECTS)])
    manifold_points_object = [np.array(cubic_splines_to_vector(manifolds_object[object_id], angle_values)) for object_id in range(constants.NUM_OBJECTS)]
    return manifold_points_universal, manifold_points_object

def test_image(image, mean_universal, mean_object, eigenvectors_universal, eigenvectors_object, manifold_points_universal, manifold_points_object, angle_values):
    image = normalize(image)
    num_components_universal = (eigenvectors_universal.shape)[1]
    projection = np.dot(image-mean_universal, eigenvectors_universal)
    distances = np.array([cdist(manifold_points_universal[object_id].T, projection.reshape(1,num_components_universal), 'euclidean') for object_id in range(constants.NUM_OBJECTS)])
    distances_minimum = np.min(distances, axis = 1)
    object_id = np.argmin(distances_minimum)
    distance = [np.min(distances[object_id])]

    num_components_object = (eigenvectors_object[object_id].shape)[1]
    projection = np.dot(image-mean_object[:, object_id], eigenvectors_object[object_id])
    distances = np.array(cdist(manifold_points_object[object_id].T, projection.reshape(1,num_components_object), 'euclidean'))
    angle_id = np.argmin(distances)
    distance.append(distances[angle_id][0])
    return object_id, angle_values[angle_id], distance

def process(DEBUGGING = False):
    function_mapping = {20 : coil_20_data_loader, 100 : coil_100_data_loader}
    print("data loading initiated") if DEBUGGING else None
    training, testing = function_mapping[constants.NUM_OBJECTS]()
    print("data loading completed...training initiated") if DEBUGGING else None
    mean_universal, mean_object, eigenvectors_universal, eigenvectors_object, manifolds_universal, manifolds_object = train_model(training)
    print("training completed...testing initiated") if DEBUGGING else None
    precision = 5
    angle_values = np.arange(0,360,precision)
    manifold_points_universal, manifold_points_object = evaluate_cubic_splines_for_angles(manifolds_universal, manifolds_object, angle_values)
    num_tests = len(testing)
    accurate_count = np.zeros(2)
    error = 0
    # print("Actual vs Estimated") if DEBUGGING else None
    for object_id_true, angle_true , image in testing:
        object_id, angle, _ = test_image(image, mean_universal, mean_object, eigenvectors_universal, eigenvectors_object, manifold_points_universal, manifold_points_object, angle_values)
        # print("Object:", [object_id_true, object_id], "Angle:", [angle_true, angle]) if DEBUGGING else None
        accurate_count[0] += (object_id_true == object_id)
        accurate_count[1] += (angle_true == angle)*(object_id_true == object_id)
        error += min(abs(angle_true - angle), 360-abs(angle_true - angle))*(object_id_true == object_id)
    print("testing completed...generating stats\n") if DEBUGGING else None
    return accurate_count[0]/num_tests, accurate_count[1]/accurate_count[0], error/accurate_count[0]

if __name__ == "__main__":
    accuracy_object, accuracy_pose, mean_error = process(True)
    print("Object Recognition accuracy: ", format(accuracy_object, ".3%"))
    print("Pose Estimation accuracy:", format(accuracy_pose, ".3%"))
    print("Mean Pose error:", format(mean_error, ".3f") + "\u00b0")
    