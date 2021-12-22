from torch.nn.utils._stateless import functional_call
from torch._expanded_weights.expanded_weights_impl import ExpandedWeight

# dependency on `functional_call` means that this can't be exposed in utils
# without creating circular dependency
def per_sample_call(module, batch_size, args, kwargs=None):
    r"""
    per_sample_call(module, batch_size, args, kwargs=None) -> Tensor
    Invoked just like a forward pass, ``per_sample_call`` will produce the same
    forward result. Then, when backward is invoked, the parameters of ``module``
    will have a ``grad_sample`` field populated with the per sample gradients
    instead of the regular gradients
    Args:
        module: The module to get per sample gradients with respect to. All trainable
          parameters will compute per sample gradients, located in a ``grad_sample``
          field when ``backward`` is invoked
        batch_size: The batch size of the input. Typically the input's first dimension
        args: Tuple of positional args passed to ``module`` to perform the forward pass
        kwargs: Dict of named args passed to ``module`` to perform the forward pass.
          Default: None
    Examples::
        >>> model = nn.Linear(4, 3)
        >>> batched_input = torch.randn(5, 4)  # batch size of 5
        >>> res = per_sample_call(model, batched_input.shape[0], batched_input).sum()
        >>> res.backward()
        >>> assert model.weight.shape == (3, 4)
        >>> assert model.weight.grad_sample.shape == (5, 3, 4)
        >>> assert model.weight.grad == None
        >>> assert model.bias.shape == (3,)
        >>> assert model.bias.grad_sample.shape == (5, 3)
        >>> assert model.bias.grad == None
    """
    def maybe_build_expanded_weight(og_tensor):
        if og_tensor.requires_grad:
            return ExpandedWeight(og_tensor, batch_size)
        else:
            return og_tensor

    params = {name: maybe_build_expanded_weight(value) for (name, value) in module.named_parameters()}
    return functional_call(module, params, args, kwargs)