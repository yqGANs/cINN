import numpy as np
from losses import maximum_mean_discrepancy
from sklearn.metrics import r2_score


def calibration_error(theta_samples, theta_test, alpha_resolution=500):
    """
    Computes the calibration error of an approximate posterior per parameters.
    The calibration error is given as the median of the absolute deviation
    between alpha (0 - 1) (credibility level) and the relative number of inliers from
    theta test.
    
    ----------
    
    Arguments:
    theta_samples       : np.ndarray of shape (n_samples, n_test, n_params) -- the samples from
                          the approximate posterior
    theta_test          : np.ndarray of shape (n_test, n_params) -- the 'true' test values
    alpha_resolution    : int -- the number of intervals to consider 
    
    ----------
    
    Returns:
    
    cal_errs  : np.ndarray of shape (n_params, ) -- the calibration errors per parameter
    """

    n_params = theta_test.shape[1]
    n_test = theta_test.shape[0]
    alphas = np.linspace(0.01, 1.0, alpha_resolution)
    cal_errs = np.zeros(n_params)
    
    # Loop for each parameter
    for k in range(n_params):
        alphas_in = np.zeros(len(alphas))
        # Loop for each alpha
        for i, alpha in enumerate(alphas):

            # Find lower and upper bounds of posterior distribution
            region = 1 - alpha
            lower = np.round(region / 2, 3)
            upper = np.round(1 - (region / 2), 3)

            # Compute quantiles for given alpha using the entire sample
            quantiles = np.quantile(theta_samples[:, :, k], [lower, upper], axis=0).T

            # Compute the relative number of inliers
            inlier_id = (theta_test[:, k] > quantiles[:, 0]) &  (theta_test[:, k] < quantiles[:, 1])
            inliers_alpha = np.sum(inlier_id) / n_test
            alphas_in[i] = inliers_alpha
        
        # Compute calibration error for k-th parameter
        diff_alphas = np.abs(alphas - alphas_in)
        cal_err = np.round(np.median(diff_alphas), 3)
        cal_errs[k] = cal_err
        
    return cal_errs

def rmse(theta_samples, theta_test, normalized=True):
    """
    Computes the RMSE or normalized RMSE (NRMSE) between posterior means 
    and true parameter values for each parameter
    
    ----------
    
    Arguments:
    theta_samples   : np.ndarray of shape (n_samples, n_test, n_params) -- the samples from
                          the approximate posterior
    theta_test      : np.ndarray of shape (n_test, n_params) -- the 'true' test values
    normalized      : boolean -- whether to compute nrmse or rmse (default True)
    
    ----------
    
    Returns:
    
    (n)rmse  : np.ndarray of shape (n_params, ) -- the (n)rmse per parameter
    """
    
    theta_approx_means = theta_samples.mean(0)
    rmse = np.sqrt( np.mean( (theta_approx_means - theta_test)**2, axis=0) )
    
    if normalized:
        rmse = rmse / (theta_test.max(axis=0) - theta_test.min(axis=0))
    return rmse


def R2(theta_samples, theta_test):
    
    """
    Computes the R^2 score as a measure of reconstruction (percentage of variance
    in true parameters captured by estimated parameters)
    
    ----------
    Arguments:
    theta_samples   : np.ndarray of shape (n_samples, n_test, n_params) -- the samples from
                          the approximate posterior
    theta_test      : np.ndarray of shape (n_test, n_params) -- the 'true' test values
    
    ----------
    Returns:
    
    r2s  : np.ndarray of shape (n_params, ) -- the r2s per parameter
    """
    
    theta_approx_means = theta_samples.mean(0)
    return r2_score(theta_test, theta_approx_means, multioutput='raw_values')


def resimulation_error(theta_samples, theta_test, simulator, **sim_args):
    """
    Computes the median deviation between data simulated with true true test parameters
    and data simulated with estimated parameters.
    
    ----------
    Arguments:
    theta_samples   : np.ndarray of shape (n_samples, n_test, n_params) -- the samples from
                          the approximate posterior
    theta_test      : np.ndarray of shape (n_test, n_params) -- the 'true' test values
    simulator       : callable -- the simulator object taking a matrix or (1, n_params) vector
                                  of parameters and returning a 3D tensor of shape (n_test, n_points, dim)
    sim_args        : arguments for the simulator
    
    ----------
    
    Returns:
    (n)rmse  : np.ndarray of shape (n_params, ) -- the (n)rmse per parameter
    """
    
    theta_approx_means = theta_samples.mean(0)
    n_test = theta_test.shape[0]

    # Simulate with true and estimated
    X_test_true = simulator(theta_test, **sim_args)
    X_test_est = simulator(theta_approx_means, **sim_args)

    # Compute MMDs
    mmds = [maximum_mean_discrepancy(X_test_true[i], X_test_est[i]) for i in range(n_test)]
    return np.median(mmds)