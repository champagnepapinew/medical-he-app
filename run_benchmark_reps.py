import benchmark
import statistics
import csv

def main():
    ns = [10, 100, 500]
    reps = 3
    summary = []
    for n in ns:
        encs = []
        hes = []
        decs = []
        plains = []
        errors = []
        for i in range(reps):
            r = benchmark.run_once(n, seed=12345 + i)
            encs.append(r['t_enc_ms'])
            hes.append(r['t_he_ms'])
            decs.append(r['t_dec_ms'])
            plains.append(r['t_plain_ms'])
            errors.append(r['error'])

        def stats(arr):
            return (statistics.mean(arr), statistics.stdev(arr) if len(arr) > 1 else 0.0)

        enc_m, enc_s = stats(encs)
        he_m, he_s = stats(hes)
        dec_m, dec_s = stats(decs)
        plain_m, plain_s = stats(plains)
        err_m, err_s = stats(errors)

        summary.append({
            'n': n,
            't_enc_mean_ms': enc_m, 't_enc_std_ms': enc_s,
            't_he_mean_ms': he_m, 't_he_std_ms': he_s,
            't_dec_mean_ms': dec_m, 't_dec_std_ms': dec_s,
            't_plain_mean_ms': plain_m, 't_plain_std_ms': plain_s,
            'error_mean': err_m, 'error_std': err_s,
        })

    keys = list(summary[0].keys())
    with open('benchmark_summary.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in summary:
            writer.writerow(row)

    print('Zapisano benchmark_summary.csv')

    # print summary
    print('n,t_enc_mean_ms±std,t_he_mean_ms±std,t_dec_mean_ms±std,t_plain_mean_ms±std,error_mean')
    for r in summary:
        print(f"{r['n']},{r['t_enc_mean_ms']:.1f}±{r['t_enc_std_ms']:.1f},{r['t_he_mean_ms']:.1f}±{r['t_he_std_ms']:.1f},{r['t_dec_mean_ms']:.1f}±{r['t_dec_std_ms']:.1f},{r['t_plain_mean_ms']:.3f}±{r['t_plain_std_ms']:.3f},{r['error_mean']:.3e}")


if __name__ == '__main__':
    main()
