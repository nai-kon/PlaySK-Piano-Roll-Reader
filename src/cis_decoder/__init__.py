try:
    from .cis_decoder import _decode_cis, _get_decode_params
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        """
        Can't import cis_decoder. You need to build cis_decoder.
        "python setup.py build_ext --inplace"
        """,
    ) from e


__all__ = [
    "_decode_cis",
    "_get_decode_params",
]
