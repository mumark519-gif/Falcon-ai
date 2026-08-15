import numpy as np


def cosine_similarity(
    vector1,
    vector2,
):

    a = np.array(vector1)
    b = np.array(vector2)

    denominator = (
        np.linalg.norm(a)
        * np.linalg.norm(b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(a, b)
        / denominator
    )