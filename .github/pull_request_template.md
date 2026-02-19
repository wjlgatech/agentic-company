## Summary

<!-- 1-3 bullet points describing what this PR changes and why -->

-
-

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / cleanup
- [ ] Documentation
- [ ] CI / tooling
- [ ] Dependency update

## How was this tested?

<!-- Describe the tests you ran. For new code, point to the test file(s). -->

```bash
# Commands run to verify this change
pytest tests/test_<relevant>.py -v
```

## Checklist

- [ ] Unit tests pass locally (`make test-unit`)
- [ ] Lint and type check pass (`make lint`)
- [ ] New code that requires real API keys is marked `@pytest.mark.integration`
- [ ] Any new workflow YAML follows the schema in CLAUDE.md
- [ ] CLAUDE.md updated if architecture or commands changed

## Related issues

<!-- Closes #123 -->
