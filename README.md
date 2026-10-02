# Radio Astronomy Imaging Tool

## Summary

This GUI was developed within the scope of the EE4795: Statistical Digital Signal Processing course for the MSc EE: SNS at the TU Delft. 
The interface provides the user with an easy way of uploading MATLAB data files containing the estimated correlation matrix of a phased array. The data then gets processed and images are produces based on the selected  
processing algorithms. The various options are discussed below.

## Imaging Algorithms

Four imaging algorithms have been implemented which are used for imaging: Matched Beamformer, Minimum Variance Distortionless Response (MVDR), CLEAN and Adapted Angular Response (AAR).

### Matched Beamformer

The matched beamformer performs a basic scan of the region of interests and returns an estimate of the power incoming from that specific direction. This is given by the formula:

$$ P(\vec{p}) = \vec{a}(\vec{p})^H R_x \vec{a} $$

where $\vec{a}$ is the steering vector and $R_x$ is the correlation matrix.
### MVDR

The MVDR beamformer is a type of beamformer that will set the response of the direction of interest to 1, while suppressing that of the other directions as much as possible. This response is given by:

$$ \displaystyle P(\vec{p}) = \cfrac{1}{\vec{a}(\vec{p})^H R^{-1}_x \vec{a}} $$

### CLEAN

The CLEAN algorithm is a way "clean-up" the dirty image formed due to the dirty beam and array geometry. The algorithm assumes the sky is mostly empty, with the exception of only a few discrete sources. The cleaned up image is a result of a sequential least-squares fitting method. It involves finding a peak in the dirty image, removing its contribution from the dirty image and repeating the process until the image left over is noise-like. This is summarized as such:

$$\begin{align}
&q = 0 \\ 
&\text{While } P(\vec{p}) \text{ is not noise-like:}\\
&\begin{cases}
q = q+1\\
\vec{p}_{q} = \underset{\vec{p}}{\text{argmax }} P_{\text{Dirty}}(\vec{p})\\
\hat{\sigma}^2_q = P_{\text{Dirty}}(\vec{p}_q)/B(\vec{0})\\
P_{\text{Dirty}}(\vec{p}) := P_{\text{Dirty}}(\vec{p}) - \gamma \hat{\sigma}^2_q B(\vec{p} - \vec{p}_q)\ \forall \vec{p}\\
\end{cases}\\
&P_{\text{Clean}}(\vec{p}) = P_{\text{Dirty}}(\vec{p}) + \displaystyle \sum_q B_{\text{Synth}}(\vec{p} - \vec{p}_q)\ \forall \vec{p}
\end{align}
$$
