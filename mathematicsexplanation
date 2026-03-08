## Batch-Level DP-SGD — Mathematical Formulation

In some practical systems, computing **per-sample gradients** is computationally expensive. Instead, **batch-level Differentially Private SGD (DP-SGD)** is used, where gradients are computed for the **entire mini-batch**, then clipped and perturbed with noise to ensure privacy.

This approach reduces computational overhead while still providing differential privacy guarantees.

---

# 1. Standard Batch Gradient in SGD

Let:

* ( \theta ) = model parameters
* ( B ) = mini-batch of size (m)
* (L(\theta, x_i)) = loss for sample (x_i)

Batch gradient:

[
g_B = \frac{1}{m}\sum_{i=1}^{m} \nabla_\theta L(\theta, x_i)
]

Model update rule:

[
\theta_{t+1} = \theta_t - \eta g_B
]

Where:

* ( \eta ) = learning rate

---

# 2. Sensitivity of Batch Gradient

Differential privacy requires controlling **sensitivity**, which measures how much the output changes when one record changes.

Sensitivity:

[
\Delta g = \max_{D,D'} || g_B(D) - g_B(D') ||_2
]

Where:

* (D) and (D') differ by one record.

To bound sensitivity, gradients must be **clipped**.

---

# 3. Batch Gradient Clipping

Instead of clipping per-sample gradients, the **entire batch gradient** is clipped.

Compute gradient norm:

[
||g_B||_2
]

Clipped gradient:

[
\tilde{g_B} =
g_B \cdot
\min\left(1, \frac{C}{||g_B||_2}\right)
]

Where:

* (C) = clipping threshold.

This ensures:

[
||\tilde{g_B}||_2 \le C
]

Thus the gradient magnitude cannot exceed the clipping bound.

---

# 4. Gaussian Noise Injection

To satisfy differential privacy, noise is added to the clipped gradient.

Noise distribution:

[
n \sim \mathcal{N}(0, \sigma^2 C^2 I)
]

Where:

* ( \sigma ) = noise multiplier
* (I) = identity matrix

Noisy gradient:

[
\hat{g_B} = \tilde{g_B} + n
]

---

# 5. Batch DP-SGD Update Rule

Final model update:

[
\theta_{t+1} =
\theta_t -
\eta
\left(
\tilde{g_B} + \mathcal{N}(0,\sigma^2 C^2 I)
\right)
]

Expanded:

[
\theta_{t+1} =
\theta_t -
\eta
\left(
g_B \cdot
\min\left(1,\frac{C}{||g_B||_2}\right)
+
\mathcal{N}(0,\sigma^2 C^2 I)
\right)
]

---

# 6. Privacy Guarantee

This mechanism satisfies **((\epsilon,\delta))-Differential Privacy**.

[
P[M(D) \in S] \le e^\epsilon P[M(D') \in S] + \delta
]

Where:

* ( \epsilon ) = privacy budget
* ( \delta ) = probability of failure.

---

# 7. Privacy Amplification by Subsampling

Since training uses **mini-batches**, privacy improves due to subsampling.

Let:

[
q = \frac{m}{N}
]

Where:

* (m) = batch size
* (N) = dataset size

Effective privacy loss decreases approximately proportional to (q).

---

# 8. Algorithm (Batch DP-SGD)

```python
for each iteration t:

    sample mini-batch B

    compute batch gradient
    g_B = ∇θ L(θ, B)

    compute norm
    norm = ||g_B||

    clip gradient
    g_clipped = g_B * min(1, C / norm)

    generate Gaussian noise
    noise ~ N(0, σ²C²)

    private gradient
    g_private = g_clipped + noise

    update parameters
    θ = θ − η * g_private
```

---

# 9. Why Batch-Level DP-SGD Is Used

Advantages:

* Lower computational cost
* Works with standard training loops
* Easier integration with custom ML models
* Suitable for **federated learning clients**

Trade-off:

* Slightly weaker privacy guarantees compared to per-sample clipping.

---

# 10. In Federated Learning Context

In a federated healthcare system:

```
Hospital Dataset
        │
Mini-Batch Training
        │
Batch Gradient
        │
Gradient Clipping
        │
Gaussian Noise (Differential Privacy)
        │
Private Model Update
        │
Upload to Federated Server
```

The central server then performs **model aggregation (e.g., Federated Averaging or ensemble aggregation)** to produce the **global model** shared across participating hospitals.

---

## Summary

Batch-level **DP-SGD** modifies standard SGD by introducing three privacy-preserving steps:

1. Compute gradients on mini-batches.
2. Clip gradient magnitude to bound sensitivity.
3. Add calibrated Gaussian noise to obscure individual data contributions.

These steps ensure that model updates remain **privacy-preserving**, enabling secure collaborative learning across distributed healthcare institutions without exposing sensitive patient data.
