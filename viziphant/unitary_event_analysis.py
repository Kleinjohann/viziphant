

import numpy
import quantities as pq
import matplotlib.pyplot as plt
import string
import neo
import elephant.unitary_event_analysis as ue

# ToDo: meaningful coloring?!
# ToDo: Input Events as neo objects/ quantities
# ToDo: check user entries
# ToDo: rearange the plotting parameters dict
# ToDo: consistent titles
# ToDo: solution for legends
# ToDo: panel sorting + selection
# ToDo: use markerdict
# ToDo: set trial labels
# ToDo: optional epochs/events + label
# ToDo: surprise representation
# ToDo: Make relation between panels clearer?!
# ToDo: set default figure settings
# ToDo: optional alphabetic labeling
# ToDo: improve neuron separation


plot_params_default = {
    # epochs to be marked on the time axis
    'events': [],
    # save figure
    'save_fig': False,
    # show figure
    'showfig': True,
    # figure size
    'figsize': (10, 12),
    # right margin
    'right': 0.9,
    # top margin
    'top': 0.9,
    # bottom margin
    'bottom': 0.1,
    # left margin
    'left': 0.1,
    # id of the units
    'unit_ids': [0, 1],
    # default line width
    'linewidth': 2,
    # delete the x ticks when "False"
    'set_xticks': False,
    # default marker size for the UEs and coincidences
    'marker_size': 4,
    # horizontal white space between subplots
    'hspace': 0.5,
    # width white space between subplots
    'wspace': 0.5,
    # font size
    'fsize': 12,
    # the actual unit ids from the experimental recording
    'unit_real_ids': [3, 2],
    # channel id
    'ch_real_ids': [],
    # line width
    'lw': 2,
    # y limit for the surprise
    'S_ylim': (-3, 3),
    # marker size for the UEs and coincidences
    'ms': 5,
    # path and file name for saving the figure
    'path_filename_format': 'figure.pdf'
}


def load_gdf2Neo(fname, trigger, t_pre, t_post):
    """
    load and convert the gdf file to Neo format by
    cutting and aligning around a given trigger
    # codes for trigger events (extracted from a
    # documentation of an old file after
    # contacting Dr. Alexa Riehle)
    # 700 : ST (correct) 701, 702, 703, 704*
    # 500 : ST (error =5) 501, 502, 503, 504*
    # 1000: ST (if no selec) 1001,1002,1003,1004*
    # 11  : PS 111, 112, 113, 114
    # 12  : RS 121, 122, 123, 124
    # 13  : RT 131, 132, 133, 134
    # 14  : MT 141, 142, 143, 144
    # 15  : ES 151, 152, 153, 154
    # 16  : ES 161, 162, 163, 164
    # 17  : ES 171, 172, 173, 174
    # 19  : RW 191, 192, 193, 194
    # 20  : ET 201, 202, 203, 204
    """

    data = numpy.loadtxt(fname)

    if trigger == 'PS_4':
        trigger_code = 114
    if trigger == 'RS_4':
        trigger_code = 124
    if trigger == 'RS':
        trigger_code = 12
    if trigger == 'ES':
        trigger_code = 15
    # specify units
    units_id = numpy.unique(data[:, 0][data[:, 0] < 7])
    # indecies of the trigger
    sel_tr_idx = numpy.where(data[:, 0] == trigger_code)[0]
    # cutting the data by aligning on the trigger
    data_tr = []
    for id_tmp in units_id:
        data_sel_units = []
        for i_cnt, i in enumerate(sel_tr_idx):
            start_tmp = data[i][1] - t_pre.magnitude
            stop_tmp = data[i][1] + t_post.magnitude
            sel_data_tmp = numpy.array(
                data[numpy.where((data[:, 1] <= stop_tmp) &
                                 (data[:, 1] >= start_tmp))])
            sp_units_tmp = sel_data_tmp[:, 1][
                numpy.where(sel_data_tmp[:, 0] == id_tmp)[0]]
            if len(sp_units_tmp) > 0:
                aligned_time = sp_units_tmp - start_tmp
                data_sel_units.append(neo.SpikeTrain(
                    aligned_time * pq.ms, t_start=0 * pq.ms,
                    t_stop=t_pre + t_post))
            else:
                data_sel_units.append(neo.SpikeTrain(
                    [] * pq.ms, t_start=0 * pq.ms,
                    t_stop=t_pre + t_post))
        data_tr.append(data_sel_units)
    data_tr.reverse()
    spiketrain = numpy.vstack([i for i in data_tr]).T
    return spiketrain


def plot_UE(data, Js_dict, sig_level, binsize, winsize, winstep,
            pattern_hash, N, plot_params_user):
    """plots Figure 1 and Figure 2 of the manuscript"""

    t_start = data[0][0].t_start
    t_stop = data[0][0].t_stop

    t_winpos = ue._winpos(t_start, t_stop, winsize, winstep)
    Js_sig = ue.jointJ(sig_level)
    num_tr = len(data)
    pat = ue.inverse_hash_from_pattern(pattern_hash, N)

    # figure format
    plot_params = plot_params_default
    plot_params.update(plot_params_user)
    globals().update(plot_params)
    if len(unit_real_ids) != N:
        raise ValueError('length of unit_ids should be' +
                         'equal to number of neurons!')
    plt.rcParams.update({'font.size': fsize})
    plt.rc('legend', fontsize=fsize)

    num_row, num_col = 6, 1
    ls = '-'
    alpha = 0.5
    plt.figure(1, figsize=figsize)
    if 'suptitle' in plot_params.keys():
        plt.suptitle("Trial aligned on " +
                     plot_params['suptitle'], fontsize=20)
    plt.subplots_adjust(top=top, right=right, left=left,
                        bottom=bottom, hspace=hspace, wspace=wspace)

    print('plotting raster plot ...')
    ax0 = plt.subplot(num_row, 1, 1)
    ax0.set_title('Spike Events')
    for n in range(N):
        for tr, data_tr in enumerate(data):
            ax0.plot(data_tr[n].rescale('ms').magnitude,
                     numpy.ones_like(data_tr[n].magnitude) *
                     tr + n * (num_tr + 1) + 1,
                     '.', markersize=0.5, color='k')
        if n < N - 1:
            ax0.axhline((tr + 2) * (n + 1), lw=2, color='k')
    ax0.set_ylim(0, (tr + 2) * (n + 1) + 1)
    ax0.set_yticks([num_tr + 1, num_tr + 16, num_tr + 31])
    ax0.set_yticklabels([1, 15, 30], fontsize=fsize)
    ax0.set_xlim(0, (max(t_winpos) + winsize).rescale('ms').magnitude)
    ax0.set_xticks([])
    ax0.set_ylabel('Trial', fontsize=fsize)
    for key in events.keys():
        for e_val in events[key]:
            ax0.axvline(e_val, ls=ls, color='r', lw=2, alpha=alpha)
    Xlim = ax0.get_xlim()
    ax0.text(Xlim[1] - 200, num_tr * 2 + 7, 'Neuron 2')
    ax0.text(Xlim[1] - 200, -12, 'Neuron 3')

    print('plotting Spike Rates ...')
    ax1 = plt.subplot(num_row, 1, 2, sharex=ax0)
    ax1.set_title('Spike Rates')
    for n in range(N):
        ax1.plot(t_winpos + winsize / 2.,
                 Js_dict['rate_avg'][:, n].rescale('Hz'),
                 label='Neuron ' + str(unit_real_ids[n]), lw=lw)
    ax1.set_ylabel('(1/s)', fontsize=fsize)
    ax1.set_xlim(0, (max(t_winpos) + winsize).rescale('ms').magnitude)
    max_val_psth = 40
    ax1.set_ylim(0, max_val_psth)
    ax1.set_yticks([0, int(max_val_psth / 2), int(max_val_psth)])
    ax1.legend(
        bbox_to_anchor=(1.12, 1.05), fancybox=True, shadow=True)
    for key in events.keys():
        for e_val in events[key]:
            ax1.axvline(e_val, ls=ls, color='r', lw=lw, alpha=alpha)
    ax1.set_xticks([])

    print('plotting Raw Coincidences ...')
    ax2 = plt.subplot(num_row, 1, 3, sharex=ax0)
    ax2.set_title('Coincident Events')
    for n in range(N):
        for tr, data_tr in enumerate(data):
            ax2.plot(data_tr[n].rescale('ms').magnitude,
                     numpy.ones_like(data_tr[n].magnitude) *
                     tr + n * (num_tr + 1) + 1,
                     '.', markersize=0.5, color='k')
            ax2.plot(
                numpy.unique(Js_dict['indices']['trial' + str(tr)]) *
                binsize,
                numpy.ones_like(numpy.unique(Js_dict['indices'][
                    'trial' + str(tr)])) * tr + n * (num_tr + 1) + 1,
                ls='', ms=ms, marker='s', markerfacecolor='none',
                markeredgecolor='c')
        if n < N - 1:
            ax2.axhline((tr + 2) * (n + 1), lw=2, color='k')
    ax2.set_ylim(0, (tr + 2) * (n + 1) + 1)
    ax2.set_yticks([num_tr + 1, num_tr + 16, num_tr + 31])
    ax2.set_yticklabels([1, 15, 30], fontsize=fsize)
    ax2.set_xlim(0, (max(t_winpos) + winsize).rescale('ms').magnitude)
    ax2.set_xticks([])
    ax2.set_ylabel('Trial', fontsize=fsize)
    for key in events.keys():
        for e_val in events[key]:
            ax2.axvline(e_val, ls=ls, color='r', lw=2, alpha=alpha)

    print('plotting emp. and exp. coincidences rate ...')
    ax3 = plt.subplot(num_row, 1, 4, sharex=ax0)
    ax3.set_title('Coincidence Rates')
    ax3.plot(t_winpos + winsize / 2.,
             Js_dict['n_emp'] / (winsize.rescale('s').magnitude * num_tr),
             label='empirical', lw=lw, color='c')
    ax3.plot(t_winpos + winsize / 2.,
             Js_dict['n_exp'] / (winsize.rescale('s').magnitude * num_tr),
             label='expected', lw=lw, color='m')
    ax3.set_xlim(0, (max(t_winpos) + winsize).rescale('ms').magnitude)
    ax3.set_ylabel('(1/s)', fontsize=fsize)
    ax3.legend(bbox_to_anchor=(1.12, 1.05), fancybox=True, shadow=True)
    YTicks = ax3.get_ylim()
    ax3.set_yticks([0, YTicks[1] / 2, YTicks[1]])
    for key in events.keys():
        for e_val in events[key]:
            ax3.axvline(e_val, ls=ls, color='r', lw=2, alpha=alpha)
    ax3.set_xticks([])

    print('plotting Surprise ...')
    ax4 = plt.subplot(num_row, 1, 5, sharex=ax0)
    ax4.set_title('Statistical Significance')
    ax4.plot(t_winpos + winsize / 2., Js_dict['Js'], lw=lw, color='k')
    ax4.set_xlim(0, (max(t_winpos) + winsize).rescale('ms').magnitude)
    ax4.axhline(Js_sig, ls='-', color='r')
    ax4.axhline(-Js_sig, ls='-', color='g')
    ax4.text(t_winpos[30], Js_sig + 0.3, '$\\alpha +$', color='r')
    ax4.text(t_winpos[30], -Js_sig - 0.5, '$\\alpha -$', color='g')
    ax4.set_xticks(t_winpos.magnitude[::int(len(t_winpos) / 10)])
    ax4.set_yticks([ue.jointJ(0.99), ue.jointJ(0.5), ue.jointJ(0.01)])
    ax4.set_yticklabels([0.99, 0.5, 0.01])

    ax4.set_ylim(S_ylim)
    for key in events.keys():
        for e_val in events[key]:
            ax4.axvline(e_val, ls=ls, color='r', lw=lw, alpha=alpha)
    ax4.set_xticks([])

    print('plotting UEs ...')
    ax5 = plt.subplot(num_row, 1, 6, sharex=ax0)
    ax5.set_title('Unitary Events')
    for n in range(N):
        for tr, data_tr in enumerate(data):
            ax5.plot(data_tr[n].rescale('ms').magnitude,
                     numpy.ones_like(data_tr[n].magnitude) *
                     tr + n * (num_tr + 1) + 1, '.',
                     markersize=0.5, color='k')
            sig_idx_win = numpy.where(Js_dict['Js'] >= Js_sig)[0]
            if len(sig_idx_win) > 0:
                x = numpy.unique(Js_dict['indices']['trial' + str(tr)])
                if len(x) > 0:
                    xx = []
                    for j in sig_idx_win:
                        xx = numpy.append(xx, x[numpy.where(
                            (x * binsize >= t_winpos[j]) &
                            (x * binsize < t_winpos[j] + winsize))])
                    ax5.plot(
                        numpy.unique(
                            xx) * binsize,
                        numpy.ones_like(numpy.unique(xx)) *
                        tr + n * (num_tr + 1) + 1,
                        ms=ms, marker='s', ls='', mfc='none', mec='r')
        if n < N - 1:
            ax5.axhline((tr + 2) * (n + 1), lw=2, color='k')
    ax5.set_yticks([num_tr + 1, num_tr + 16, num_tr + 31])
    ax5.set_yticklabels([1, 15, 30], fontsize=fsize)
    ax5.set_ylim(0, (tr + 2) * (n + 1) + 1)
    ax5.set_xlim(0, (max(t_winpos) + winsize).rescale('ms').magnitude)
    ax5.set_xticks([])
    ax5.set_ylabel('Trial', fontsize=fsize)
    ax5.set_xlabel('Time [ms]', fontsize=fsize)
    for key in events.keys():
        for e_val in events[key]:
            ax5.axvline(e_val, ls=ls, color='r', lw=2, alpha=alpha)
            ax5.text(e_val - 10 * pq.ms,
                     S_ylim[0] - 35, key, fontsize=fsize, color='r')
    ax5.set_xticks([])

    for i in range(num_row):
        ax = locals()['ax' + str(i)]
        ax.text(-0.05, 1.1, string.ascii_uppercase[i],
                transform=ax.transAxes, size=fsize + 5,
                weight='bold')
    if plot_params['save_fig']:
        plt.savefig(path_filename_format)
        if not showfig:
            plt.cla()
            plt.close()

    if showfig:
        plt.show()

    return None



