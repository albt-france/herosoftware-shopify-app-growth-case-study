"""A/B-test statistics used in the notebook and the report. Plain NumPy/SciPy, one function per idea,
so every number can be re-derived by hand.

  sample_size_prop     users per arm to detect a relative lift on a conversion rate
  sample_size_mean     users per arm to detect a relative lift on a mean (revenue, messages)
  prop_test            difference of two proportions: z-test, 95% CI (absolute and relative)
  mean_test            difference of two means: Welch t-test, 95% CI (absolute and relative, delta method)
  srm_test             sample-ratio mismatch: chi-square goodness of fit
  adjust_pvalues       Bonferroni, Holm and Benjamini-Hochberg corrections
  cuped                CUPED variance reduction with a pre-period covariate
  obf_boundary         O'Brien-Fleming z boundary for repeated looks (constant calibrated by simulation)
  peeking_fpr          false-positive rate of "stop at the first p < 0.05" in A/A simulations
"""
import numpy as np
from scipy import stats

Z = stats.norm.ppf


def sample_size_prop(p_base, rel_mde, alpha=0.05, power=0.80):
    """n per arm for a two-sided z-test on proportions: n = (z_a/2 + z_b)^2 * (p1 q1 + p2 q2) / (p2 - p1)^2."""
    p2 = p_base * (1 + rel_mde)
    num = (Z(1 - alpha / 2) + Z(power)) ** 2 * (p_base * (1 - p_base) + p2 * (1 - p2))
    return int(np.ceil(num / (p2 - p_base) ** 2))


def sample_size_mean(mean_base, sd, rel_mde, alpha=0.05, power=0.80):
    """n per arm for a two-sided test on means with equal variance: n = 2 (z_a/2 + z_b)^2 sd^2 / delta^2."""
    delta = mean_base * rel_mde
    return int(np.ceil(2 * (Z(1 - alpha / 2) + Z(power)) ** 2 * sd ** 2 / delta ** 2))


def mde_mean(mean_base, sd, n_per_arm, alpha=0.05, power=0.80):
    """Smallest relative lift detectable with n users per arm."""
    return (Z(1 - alpha / 2) + Z(power)) * sd * np.sqrt(2 / n_per_arm) / mean_base


def prop_test(x_t, n_t, x_c, n_c, alpha=0.05):
    p_t, p_c = x_t / n_t, x_c / n_c
    se = np.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)          # unpooled SE for the CI
    p_pool = (x_t + x_c) / (n_t + n_c)
    se0 = np.sqrt(p_pool * (1 - p_pool) * (1 / n_t + 1 / n_c))            # pooled SE for the test
    z = (p_t - p_c) / se0
    d = p_t - p_c
    zc = Z(1 - alpha / 2)
    rel_se = np.sqrt((p_t * (1 - p_t) / n_t) / p_c ** 2 + (p_t ** 2) * (p_c * (1 - p_c) / n_c) / p_c ** 4)
    return dict(n_t=int(n_t), n_c=int(n_c), rate_t=p_t, rate_c=p_c, diff=d, ci_low=d - zc * se, ci_high=d + zc * se,
                rel=d / p_c, rel_low=d / p_c - zc * rel_se, rel_high=d / p_c + zc * rel_se, z=z, p=2 * stats.norm.sf(abs(z)))


def mean_test(y_t, y_c, alpha=0.05):
    y_t, y_c = np.asarray(y_t, float), np.asarray(y_c, float)
    m_t, m_c = y_t.mean(), y_c.mean()
    v_t, v_c = y_t.var(ddof=1) / len(y_t), y_c.var(ddof=1) / len(y_c)
    se = np.sqrt(v_t + v_c)
    dof = (v_t + v_c) ** 2 / (v_t ** 2 / (len(y_t) - 1) + v_c ** 2 / (len(y_c) - 1))
    t = (m_t - m_c) / se
    tc = stats.t.ppf(1 - alpha / 2, dof)
    d = m_t - m_c
    rel_se = np.sqrt(v_t / m_c ** 2 + m_t ** 2 * v_c / m_c ** 4)             # delta method for (m_t / m_c - 1)
    return dict(n_t=len(y_t), n_c=len(y_c), mean_t=m_t, mean_c=m_c, diff=d, ci_low=d - tc * se, ci_high=d + tc * se,
                rel=d / m_c, rel_low=d / m_c - tc * rel_se, rel_high=d / m_c + tc * rel_se, se=se, t=t,
                p=2 * stats.t.sf(abs(t), dof))


def srm_test(n_t, n_c, expected_t=0.5):
    n = n_t + n_c
    chi2 = (n_t - n * expected_t) ** 2 / (n * expected_t) + (n_c - n * (1 - expected_t)) ** 2 / (n * (1 - expected_t))
    return dict(n_t=int(n_t), n_c=int(n_c), share_t=n_t / n, chi2=chi2, p=stats.chi2.sf(chi2, 1))


def adjust_pvalues(p):
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    bonf = np.minimum(p * m, 1)
    holm = np.empty(m)
    holm[order] = np.minimum(1, np.maximum.accumulate((m - np.arange(m)) * p[order]))
    bh = np.empty(m)
    ranked = p[order] * m / (np.arange(m) + 1)
    bh[order] = np.minimum(1, np.minimum.accumulate(ranked[::-1])[::-1])
    return dict(bonferroni=bonf, holm=holm, bh=bh)


def cuped(y, x, treat):
    """theta = cov(x, y) / var(x) on the pooled sample; y_adj = y - theta (x - mean x). Same mean, smaller variance."""
    y, x, treat = np.asarray(y, float), np.asarray(x, float), np.asarray(treat, bool)
    theta = np.cov(x, y, ddof=1)[0, 1] / x.var(ddof=1)
    y_adj = y - theta * (x - x.mean())
    rho = np.corrcoef(x, y)[0, 1]
    return dict(theta=theta, rho=rho, var_reduction=1 - y_adj.var(ddof=1) / y.var(ddof=1),
                raw=mean_test(y[treat], y[~treat]), adjusted=mean_test(y_adj[treat], y_adj[~treat]), y_adj=y_adj)


def obf_constant(n_looks, alpha=0.05, n_sims=200_000, seed=11):
    """O'Brien-Fleming boundary z_k = C / sqrt(t_k) for n_looks equally spaced looks. C is calibrated by
    simulating the cumulative z-statistic under the null (a scaled random walk) so that the chance of ever
    crossing is alpha. For one look C = 1.96; it grows with the number of looks."""
    rng = np.random.default_rng(seed)
    k = np.arange(1, n_looks + 1)
    z = np.cumsum(rng.standard_normal((n_sims, n_looks)), axis=1) / np.sqrt(k)
    stat = np.max(np.abs(z) * np.sqrt(k / n_looks), axis=1)      # crossing |z_k| > C / sqrt(t_k)  <=>  |z_k| sqrt(t_k) > C
    return float(np.quantile(stat, 1 - alpha))


def obf_boundary(info_frac, alpha=0.05):
    """z boundary at each look (information fractions t_k, equally spaced): C / sqrt(t_k)."""
    t = np.asarray(info_frac, float)
    return obf_constant(len(t), alpha) / np.sqrt(t)


def peeking_fpr(n_per_day, days, p_base, n_sims=2000, alpha=0.05, seed=7):
    """A/A simulations: share of tests that ever show p < alpha when read every day (naive) vs once at the end,
    and with the O'Brien-Fleming boundary."""
    rng = np.random.default_rng(seed)
    zc = Z(1 - alpha / 2)
    frac = np.arange(1, days + 1) / days
    bound = obf_boundary(frac, alpha)
    ever = end = obf = 0
    for _ in range(n_sims):
        xt = rng.binomial(n_per_day, p_base, days).cumsum()
        xc = rng.binomial(n_per_day, p_base, days).cumsum()
        n = n_per_day * np.arange(1, days + 1)
        pp = (xt + xc) / (2 * n)
        z = (xt / n - xc / n) / np.sqrt(pp * (1 - pp) * 2 / n)
        ever += np.any(np.abs(z) > zc)
        end += abs(z[-1]) > zc
        obf += np.any(np.abs(z) > bound)
    return dict(naive_daily=ever / n_sims, single_look=end / n_sims, obf_daily=obf / n_sims, n_sims=n_sims)
