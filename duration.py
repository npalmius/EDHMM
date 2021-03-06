import numpy as np
import logging

log = logging.getLogger('duration') 

class Poisson:
    def __init__(self, mu, alpha, beta, support_step=1):
        self.alpha = alpha
        self.beta = beta
        self.mu = mu
        self.states = range(len(mu))
        self.support_step = support_step
    
    def likelihood(self,state,k):
        assert state in self.states
        return (k*np.log(self.mu[state])) - sum([np.log(ki+1) for ki in range(k)]) - self.mu[state]
    
    def sample_d(self, state):
        return np.random.poisson(self.mu[state])
    
    def sample_mu(self, Zs):
        
        k = dict([(i,[]) for i in self.states])
        
        for Z in Zs:
            X = [z[0] for z in Z]
            now = X[0]
            for s in X:
                if now == s:
                    try:
                        k[now][-1] += 1
                    except IndexError:
                        # initial condition
                        k[now] = [1]
                else:
                    now = s
                    k[now].append(1)
        
        for i in self.states:
            log.debug("state: %s"%i)
            log.debug("observations: %s"%k[i])
        
        out=[]
        for i in self.states:
            alpha = self.alpha[i] + sum(k[i])
            beta = self.beta[i] + len(k[i])
            log.debug('drawing mu from a gamma with alpha=%s and beta=%s'%(alpha,beta))
            out.append(np.random.gamma(alpha, 1.0/beta))
            log.debug('sampled rate parameter for state %s: %s'%(i,out[-1]))
            if out[-1] > 1000:
                print alpha # 1
                print beta #  0.00001
        return out
    
    def update(self, Z):
        self.mu = self.sample_mu(Z)
    
    def support(self, state, threshold=0.00001):
        log.info('finding support for state %s'%state)
        # walk left
        d, dl = int(self.mu[state]), 1
        lold = self.likelihood(state,d)
        while dl > threshold:
            lnew = np.exp(self.likelihood(state,d))
            dl = abs(lnew-lold)
            lold = lnew
            d -= self.support_step
        left = max(1,d)
        # walk right
        d, dl = int(self.mu[state]), 1
        lold = self.likelihood(state,d)
        while dl > threshold:
            d += self.support_step
            lnew = np.exp(self.likelihood(state,d))
            dl = abs(lnew-lold)
            lold = lnew
        right = max(1,d)
        log.debug('support for state %s: %s to %s'%(state,int(left),int(right)))
        return int(left), int(right)
        
        
if __name__ == "__main__":
    import pylab as pb
    Z = np.load('Z.npy')
    D = Poisson(
        mu = [1, 1, 1], 
        alpha=[1, 1, 1],
        beta=[0.0001, 0.0001, 0.0001]
    )
    pb.figure()
    for j in range(3):
        mus = np.array([D.sample_mu([Z])[j] for i in range(100)])
        pb.hist(mus,alpha=0.5)
    
    
    pb.figure()
    for j in range(3):
        d = []
        for i in range(1000):
            D.update([Z])
            d.append(D.sample_d(j))
        pb.hist(d,alpha=0.5)
    
    pb.show()