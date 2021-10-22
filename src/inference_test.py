import argparse
from pathlib import Path
import time

import numpy as np

from utils.util import fix_seed
from utils.trt import (
    load_engine,
    allocate_buffers,
    do_inference_v2,
    load_data,
)


def get_argparser() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-path", type=str)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    return args


def get_dummy_input(
    batch_size: int,
    color_size: int,
    hetigh_size: int,
    width_size: int,
) -> np.ndarray:
    input_shape_size = (
        batch_size,
        color_size,
        hetigh_size,
        width_size,
    )
    input_data = np.random.randint(0, 255, input_shape_size)
    return input_data


def preprocess(input_data: np.ndarray) -> np.ndarray:
    input_data = input_data.astype(np.float32)
    input_data = input_data / 255
    input_data[:, 0, :, :] = (input_data[:, 0, :, :] - 0.485) / 0.229
    input_data[:, 1, :, :] = (input_data[:, 1, :, :] - 0.456) / 0.224
    input_data[:, 2, :, :] = (input_data[:, 2, :, :] - 0.406) / 0.225
    return input_data.ravel()


if __name__ == "__main__":
    args = get_argparser()
    fix_seed(args.seed)
    engine_path = Path(args.engine_path)
    if not engine_path.is_file():
        raise Exception(f"File Not Found. {str(engine_path)}")

    engine = load_engine(engine_path)
    context = engine.create_execution_context()
    inputs, outputs, bindings, stream = allocate_buffers(engine)

    input_data = get_dummy_input(1, 3, 224, 224)
    input_data = preprocess(input_data)

    start = time.time()
    load_data(input_data, inputs[0].host)

    res_prob = do_inference_v2(
        context=context,
        bindings=bindings,
        inputs=inputs,
        outputs=outputs,
        stream=stream,
    )
    res_cls = res_prob[0].reshape((1, 1000)).argmax()
    print(f"inference: {time.time() - start} [sec]")

    print(res_cls)
