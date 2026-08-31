# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-08-28 12:23

@author: a002028

"""
import seaborn as sns
sns.set_style("ticks", {'axes.grid': True, 'grid.linestyle': '--'})
sns.set_context("paper", rc={"grid.linewidth": 0.5})
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
import cmocean
import numpy as np

from bawsvis.paths import data_dir


def gshhs_coastline_path():
    """High-resolution GSHHS land polygons used to mask land in maps."""
    path = data_dir('shape') / 'GSHHS_h_L1.shp'
    if not path.exists():
        raise FileNotFoundError(
            f'Missing coastline shapefile: {path}\n'
            'Download gshhg-shp from '
            'https://www.soest.hawaii.edu/pwessel/gshhg/ and place '
            'GSHHS_shp/h/GSHHS_h_L1.* there.'
        )
    return path


class PlotMap:
    """
    """
    def __init__(self, data_mat=False,
                 lat_mat=False,
                 lon_mat=False,
                 mask=False,
                 year=False,
                 cbar_label='',
                 cmap_step=2,
                 max_tick=20,
                 min_tick=0,
                 cmap=None,
                 max_min_range=False,
                 set_maxmin_from_data=False,
                 use_frame=False,
                 map_frame={'lat_min': 53.5, 'lat_max': 66., 'lon_min': 9., 'lon_max': 31.},
                 delta_lat=False,
                 delta_lon=False,
                 resolution='i',
                 text=False,
                 show_fig=False,
                 save_fig=False,
                 fig_name='figure',
                 fig_title=False,
                 save_dir='',
                 clear_fig=False,
                 p_color=False):

        self.color_map = cmap or plt.cm.viridis #plt.cm.jet viridis_r = reversed version of colors
        self.data = data_mat
        self.mask = mask

        if delta_lat:
            self.delta_lat = delta_lat
        else:
            self.delta_lat = 2
        if delta_lat:
            self.delta_lon = delta_lon
        else:
            self.delta_lon = 4

        self.resolution = resolution
        self.text = text
        self.save_dir = save_dir
        if fig_title:
            self.fig_title = fig_title
        elif year:
            self.fig_title = 'Number of days with surface \naccumulations of cyanobacteria during ' + year

        self.cbar_label = cbar_label
        if max_min_range:
            self.min_tick = max_min_range[0]
            self.max_tick = max_min_range[1]
            self.cmap_step = self.max_tick / 10.
        else:
            self.cmap_step = cmap_step
            self.max_tick = max_tick
            self.min_tick = min_tick

        if year:
            print('Plotting for year:', year)

        self.map_frame = map_frame
        self.use_frame = use_frame

        # self._draw_map()
        #
        # self._draw_mesh(p_color)

        if show_fig:
            plt.show()
        if save_fig:
            self._save_figure(fig_name)
        if clear_fig:
            plt.close('all')

    def _draw_map(self, lat_mat=False, lon_mat=False,):
        print('Drawing map...')
        self.map_figure = plt.figure()
        self.map_axes = self.map_figure.add_subplot(111)
        self.plot_type = 'field'

        self.map = Basemap(projection='stere', boundinglat=53, lon_0=19, lat_0=60, resolution=self.resolution,
                           area_thresh=1.,
                           llcrnrlat=self.map_frame['lat_min'], urcrnrlat=self.map_frame['lat_max'],
                           llcrnrlon=self.map_frame['lon_min'], urcrnrlon=self.map_frame['lon_max'],
                           ax=self.map_axes)
        self.x, self.y = self.map(lon_mat, lat_mat)
        # import geopandas as gp
        # gf = gp.read_file(r'C:\Temp\baws_tempo\lake_mask.shp')
        # for geom in gf.geometry:
        #     x, y = self.map(geom.exterior.coords.xy[0], geom.exterior.coords.xy[1])
        #     poly = Polygon(
        #         np.array([x, y]).T,
        #         # facecolor='#E1E0DD',
        #         # edgecolor='#E1E0DD',
        #         facecolor='w',
        #         edgecolor='w',
        #         zorder=3,
        #         linewidth=0.
        #     )
        #     self.map_axes.add_patch(poly)

        #        self.map = Basemap(llcrnrlon=self.map_frame['lon_min'],
        #                           llcrnrlat=self.map_frame['lat_min'],
        #                           urcrnrlon=self.map_frame['lon_max'],
        #                           urcrnrlat=self.map_frame['lat_max'],
        #                           resolution=self.resolution,
        #                           projection='merc',
        #                           area_thresh=100.,
        #                           ax=self.map_axes)

        self.map.drawcoastlines(linewidth=0.25)
        # self.map.drawcountries(linewidth=0.15)
        #        self.map.fillcontinents(color=[0.7, 0.7, 0.7])
        #        self.map.fillcontinents(color='#000000', lake_color='#C6E2FF')
        # self.map.fillcontinents(color='#ECEBE6', lake_color='#B3C6D4')
        # self.map.fillcontinents(color='#E1E0DD')
        self.map.fillcontinents(color='k', lake_color='k')
        # self.map.drawmapboundary(fill_color='#B3C6D4')
        #        self.map.drawrivers(linewidth=1, linestyle='solid',
        #                            color='b', antialiased=1)

        self.map.drawparallels(np.arange(-81., 82., 2.), linewidth=0.3,
                               labels=[False, False, False, False])  # labels=[True,False, False, False])
        self.map.drawmeridians(np.arange(-177., 181., 4.), linewidth=0.3,
                               labels=[False, False, False, False])  # labels=[False, False, False, True])

        if self.use_frame:
            self.map_axes.spines['right'].set_color('white')
            self.map_axes.spines['left'].set_color('white')
            self.map_axes.spines['top'].set_color('white')
            self.map_axes.spines['bottom'].set_color('white')

            drawframe(BaseMap=self.map,  # Basemap object
                      ax=self.map_axes)

    def plot_patches(self, patches):
        """
        :return:
        """
        if any(patches):
            self.map_axes.add_collection(PatchCollection(patches, match_original=True))

    def set_label_text(self, text):
        self.text = text

    def _draw_mesh(self, p_color=False, data_mat=None):
        print('Drawing mesh..')
        self.data = data_mat
        # self.data[self.data <= 0] = np.nan
        # Create 2D lat/lon arrays for Basemap
        #        lon2d, lat2d = np.meshgrid(self.lons, self.lats)
        # Transforms lat/lon into plotting coordinates for projection
        # self.min_val = self.data[np.where(np.isfinite(self.data))].min()
        # self.max_val = self.data[np.where(np.isfinite(self.data))].max()
        print(self.data.type())
        self.min_val = self.data[np.where(np.isfinite(self.data))].min()
        self.max_val = self.data[np.where(np.isfinite(self.data))].max()
        self.extend = 'max'

        self.map_color_range = np.linspace(self.min_tick, self.max_tick,
                                           500, endpoint=False)
        self.map_tick_list = list(np.arange(self.min_tick, self.max_tick,
                                            self.cmap_step))

        if p_color:
            self.map_mesh = self.map_axes.pcolormesh(self.x, self.y, self.data,
                                                     cmap=self.color_map,
                                                     vmin=self.min_tick,
                                                     vmax=self.max_tick)
            #
            #            self.map_mesh.cmap.set_under('white')
            self.map_mesh.cmap.set_under('#C6E2FF')

            cbar = plt.colorbar(self.map_mesh,
                                extend=self.extend,
                                orientation='vertical',
                                shrink=0.8)

            cbar.set_label(self.cbar_label)

        else:
            self.map_mesh = self.map_axes.contourf(self.x, self.y, self.data,
                                                   self.map_color_range,
                                                   cmap=self.color_map,
                                                   extend=self.extend,
                                                   interpolation='nearest')

            cbar = plt.colorbar(self.map_mesh, ticks=self.map_tick_list,
                                orientation='vertical', shrink=0.8)

            cbar.set_label(self.cbar_label)

        if self.text:
            self._add_text_box(self.map_axes, self.text)
        #        cbar.set_label('hej')

        if hasattr(self, 'fig_title'):
            plt.title(self.fig_title, fontsize=10)

    def _add_text_box(self, ax, textstr):
        # these are matplotlib.patch.Patch properties
        props = dict(facecolor='white', alpha=0.8)
        # 0.565, 0.966
        # 0.040, 0.966
        # place a text box in upper left in axes coords
        ax.text(0.5, 0.966, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='left',
                bbox=props,
                zorder=21)

    def _save_figure(self, name='test_png_i.png'):
        plt.tight_layout()
        plt.savefig(name, bbox_inches='tight', dpi=600)


class PlotWhiteMap:
    """Doc."""

    def __init__(self, data_mat=False,
                 lat_mat=False,
                 lon_mat=False,
                 mask=False,
                 year=False,
                 cbar_label='',
                 cmap_step=2,
                 max_tick=20,
                 min_tick=0,
                 cmap=None,
                 max_min_range=False,
                 set_maxmin_from_data=False,
                 map_frame={'lat_min': 53.5, 'lat_max': 66., 'lon_min': 9., 'lon_max': 31.},
                 delta_lat=False,
                 delta_lon=False,
                 resolution='i',
                 text=False,
                 fig_title=False
                 ):

        self.color_map = cmap or plt.cm.viridis # viridis_r = reversed version of colors
        self.data = data_mat
        self.lats = lat_mat
        self.lons = lon_mat
        self.mask = mask

        if delta_lat:
            self.delta_lat = delta_lat
        else:
            self.delta_lat = 2
        if delta_lat:
            self.delta_lon = delta_lon
        else:
            self.delta_lon = 4

        self.resolution = resolution
        self.text = text
        if fig_title:
            self.fig_title = fig_title
        elif year:
            self.fig_title = 'Number of days with surface \naccumulations of cyanobacteria during ' + year

        self.cbar_label = cbar_label
        if max_min_range:
            self.min_tick = max_min_range[0]
            self.max_tick = max_min_range[1]
            self.cmap_step = self.max_tick / 10.
        else:
            if set_maxmin_from_data:
                self.min_tick = self.data[np.where(np.isfinite(self.data))].min()
                self.max_tick = self.data[np.where(np.isfinite(self.data))].max()
                self.cmap_step = self.max_tick / 10.
            else:
                self.cmap_step = cmap_step
                self.max_tick = max_tick
                self.min_tick = min_tick

        if year:
            print('Plotting for year:', year)

        self.map_frame = map_frame

    def _draw_map(self):
        print('Drawing map...')
        self.data[self.data <= 0] = np.nan
        self.map_figure = plt.figure()
        self.map_axes = self.map_figure.add_subplot(111)
        self.plot_type = 'field'

        self.map = Basemap(projection='stere', boundinglat=54, lon_0=11, lat_0=60,
                           resolution=self.resolution,
                           area_thresh=1.,
                           llcrnrlat=self.map_frame['lat_min'], urcrnrlat=self.map_frame['lat_max'],
                           llcrnrlon=self.map_frame['lon_min'], urcrnrlon=self.map_frame['lon_max'],
                           ax=self.map_axes)

        import geopandas as gp
        gf = gp.read_file(gshhs_coastline_path())
        # Only land polygons touching the map frame matter; the global
        # dataset has ~180k polygons and drawing them all takes forever.
        gf = gf.cx[self.map_frame['lon_min'] - 2:self.map_frame['lon_max'] + 2,
                   self.map_frame['lat_min'] - 2:self.map_frame['lat_max'] + 2]
        for geom in gf.geometry:
            x, y = self.map(geom.exterior.coords.xy[0], geom.exterior.coords.xy[1])
            poly = Polygon(
                np.array([x, y]).T,
                facecolor='w',
                edgecolor='w',
                zorder=3,
                linewidth=0.
            )
            self.map_axes.add_patch(poly)

        self.map.drawcoastlines(linewidth=0.25)
        self.map.drawcountries(linewidth=0.15)
        self.map.fillcontinents(color='w')

    def plot_patches(self, patches):
        """
        :return:
        """
        if any(patches):
            self.map_axes.add_collection(PatchCollection(patches, match_original=True))

    def _draw_mesh(self, p_color=False):
        print('Drawing mesh..')
        x, y = self.map(self.lons, self.lats)
        self.min_val = self.data[np.where(np.isfinite(self.data))].min()
        self.max_val = self.data[np.where(np.isfinite(self.data))].max()
        self.extend = 'max'

        self.map_color_range = np.linspace(self.min_tick, self.max_tick,
                                           500, endpoint=False)
        self.map_tick_list = list(np.arange(self.min_tick, self.max_tick + self.cmap_step,
                                            self.cmap_step))
        if p_color:
            self.map_mesh = self.map_axes.pcolormesh(x, y, self.data,
                                                     cmap=self.color_map,
                                                     vmin=self.min_tick,
                                                     vmax=self.max_tick)

            self.map_mesh.cmap.set_under('#C6E2FF')

            cax = self.map_axes.inset_axes([.8, 0.05, 0.03, 0.45],
                                           transform=self.map_axes.transAxes)
            cbar = plt.colorbar(self.map_mesh, ticks=self.map_tick_list,
                                orientation='vertical', shrink=0.8,
                                extend=self.extend,
                                ax=self.map_axes, cax=cax)

            cbar.set_label(self.cbar_label)

        else:
            self.map_mesh = self.map_axes.contourf(x, y, self.data,
                                                   self.map_color_range,
                                                   cmap=self.color_map,
                                                   extend=self.extend,
                                                   interpolation='nearest')
            cax = self.map_axes.inset_axes([1.04, 0.2, 0.05, 0.6],
                                           transform=self.map_axes.transAxes)
            cbar = plt.colorbar(self.map_mesh, ticks=self.map_tick_list,
                                orientation='vertical', shrink=0.8,
                                ax=self.map_axes, cax=cax)

            cbar.set_label(self.cbar_label)

        if self.text:
            self._add_text_box(self.map_axes, self.text)

        if hasattr(self, 'fig_title'):
            plt.title(self.fig_title, fontsize=10)

    def hide_axis(self):
        plt.axis('off')

    def _add_text_box(self, ax, textstr):
        # these are matplotlib.patch.Patch properties
        props = dict(facecolor='white', alpha=0.8)
        # 0.565, 0.966
        # place a text box in upper left in axes coords
        ax.text(0.6, 0.7, textstr, transform=ax.transAxes, fontsize=30,
                # verticalalignment='top', horizontalalignment='left',
                bbox=props,
                zorder=21)

    def _save_figure(self, name='test_png_i.png'):
        plt.tight_layout()
        plt.savefig(name, bbox_inches='tight', dpi=600)
        plt.close()


class PlotIceMap:
    """
    """
    def __init__(self, data_mat=False,
                 lat_mat=False,
                 lon_mat=False,
                 mask=False,
                 year=False,
                 cbar_label='',
                 cmap_step=2,
                 cmap=None,
                 max_tick=20,
                 min_tick=0,
                 max_min_range=False,
                 set_maxmin_from_data=False,
                 use_frame=False,
                 map_frame={'lat_min': 53.5, 'lat_max': 66., 'lon_min': 9., 'lon_max': 31.},
                 delta_lat=False,
                 delta_lon=False,
                 resolution='i',
                 text=False,
                 show_fig=False,
                 save_fig=False,
                 fig_name='figure',
                 fig_title=False,
                 save_dir='',
                 clear_fig=False,
                 p_color=False):
        self.color_map = cmap or plt.cm.viridis # viridis_r = reversed version of colors
        self.data = data_mat
        self.lats = lat_mat
        self.lons = lon_mat
        self.mask = mask

        if delta_lat:
            self.delta_lat = delta_lat
        else:
            self.delta_lat = 2
        if delta_lat:
            self.delta_lon = delta_lon
        else:
            self.delta_lon = 4

        self.resolution = resolution
        self.text = text
        self.save_dir = save_dir
        if fig_title:
            self.fig_title = fig_title
        elif year:
            self.fig_title = 'Number of days with surface \naccumulations of cyanobacteria during ' + year

        self.cbar_label = cbar_label
        if max_min_range:
            self.min_tick = max_min_range[0]
            self.max_tick = max_min_range[1]
            self.cmap_step = self.max_tick / 10.
        else:
            if set_maxmin_from_data:
                self.min_tick = self.data[np.where(np.isfinite(self.data))].min()
                self.max_tick = self.data[np.where(np.isfinite(self.data))].max()
                self.cmap_step = self.max_tick / 10.
            else:
                self.cmap_step = cmap_step
                self.max_tick = max_tick
                self.min_tick = min_tick

        if year:
            print('Plotting for year:', year)

        self.map_frame = map_frame
        self.use_frame = use_frame

        # self._draw_map()
        #
        # self._draw_mesh(p_color)
        #
        # if show_fig:
        #     plt.show()
        # if save_fig:
        #     self._save_figure(fig_name)
        # if clear_fig:
        #     plt.close('all')

    def _draw_map(self):
        print('Drawing map...')
        # self.data[self.data <= 0] = np.nan
        self.map_figure = plt.figure()
        self.map_axes = self.map_figure.add_subplot(111)
        self.plot_type = 'field'

        self.map = Basemap(projection='stere', boundinglat=53, lon_0=20, lat_0=60, resolution=self.resolution,
                           area_thresh=1.,
                           llcrnrlat=self.map_frame['lat_min'], urcrnrlat=self.map_frame['lat_max'],
                           llcrnrlon=self.map_frame['lon_min'], urcrnrlon=self.map_frame['lon_max'],
                           ax=self.map_axes)

        import geopandas as gp
        gf = gp.read_file(r'C:\Temp\baws_tempo\lake_mask.shp')
        boolean = gf['class'].isin([1, 2])
        for geom in gf.geometry[boolean]:
            x, y = self.map(geom.exterior.coords.xy[0], geom.exterior.coords.xy[1])
            poly = Polygon(np.array([x, y]).T, facecolor='w', edgecolor='w', zorder=3, linewidth=0.)
            self.map_axes.add_patch(poly)

        self.map.drawparallels(np.arange(-81., 82., 2.), linewidth=0.3,
                               labels=[False, False, False, False])  # labels=[True,False, False, False])
        self.map.drawmeridians(np.arange(-177., 181., 4.), linewidth=0.3,
                               labels=[False, False, False, False])  # labels=[False, False, False, True])

        self.map.drawcoastlines(linewidth=0.25, zorder=2)
        # self.map.drawcountries(linewidth=0.15, zorder=9)

        if self.use_frame:
            self.map_axes.spines['right'].set_color('white')
            self.map_axes.spines['left'].set_color('white')
            self.map_axes.spines['top'].set_color('white')
            self.map_axes.spines['bottom'].set_color('white')

            drawframe(
                BaseMap=self.map,  # Basemap object
                ax=self.map_axes
            )

    def plot_patches(self, patches):
        if any(patches):
            self.map_axes.add_collection(PatchCollection(patches, match_original=True))

    def _draw_mesh(self, p_color=False):
        print('Drawing mesh..')

        from matplotlib.colors import LinearSegmentedColormap

        # color = cmocean.cm.thermal(np.linspace(1, 0.2, 256))
        # color = cmocean.cm.ice(np.linspace(0.8, 0.2, 256))
        # cmappen = LinearSegmentedColormap.from_list('cm_smhi_ice', color)
        # cmappen = cmocean.cm.thermal
        cmappen = cmocean.cm.haline
        # cmappen = plt.cm.jet

        # Transforms lat/lon into plotting coordinates for projection
        x, y = self.map(self.lons, self.lats)
        # self.color_map = plt.cm.jet
        # self.color_map = cmappen
        self.min_val = self.data[np.where(np.isfinite(self.data))].min()
        self.max_val = self.data[np.where(np.isfinite(self.data))].max()
        # self.extend = 'max'
        self.extend = 'both'

        self.map_color_range = np.linspace(self.min_tick, self.max_tick,
                                           500, endpoint=False)
        self.map_tick_list = list(np.arange(self.min_tick, self.max_tick,
                                            self.cmap_step))

        if p_color:
            self.map_mesh = self.map_axes.pcolormesh(x, y, self.data,
                                                     cmap=self.color_map,
                                                     vmin=self.min_tick,
                                                     vmax=self.max_tick)
            #
            #            self.map_mesh.cmap.set_under('white')
            # self.map_mesh.cmap.set_under('#C6E2FF')

            cbar = plt.colorbar(self.map_mesh,
                                extend=self.extend,
                                orientation='vertical',
                                shrink=0.8)

            cbar.set_label(self.cbar_label)

        else:
            self.map_mesh = self.map_axes.contourf(x, y, self.data,
                                                   self.map_color_range,
                                                   cmap=self.color_map,
                                                   extend=self.extend,
                                                   interpolation='nearest')
            cbar = plt.colorbar(self.map_mesh, ticks=self.map_tick_list,
                                orientation='vertical', shrink=0.8)

            cbar.set_label(self.cbar_label)

        if self.text:
            self._add_text_box(self.map_axes, self.text)
        #        cbar.set_label('hej')

        if hasattr(self, 'fig_title'):
            plt.title(self.fig_title, fontsize=10)

    def _add_text_box(self, ax, textstr):
        # these are matplotlib.patch.Patch properties
        props = dict(facecolor='white', alpha=0.8)
        # 0.565, 0.966
        # place a text box in upper left in axes coords
        ax.text(0.040, 0.966, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='left',
                bbox=props,
                zorder=21)

    def _save_figure(self, name='test_png_i.png'):
        plt.tight_layout()
        plt.savefig(name, bbox_inches='tight', dpi=300)


class PlotBasinPatchesMap:
    """Doc."""

    def __init__(self, mask=False, map_frame=None, resolution='i', text=False, fig_title=False,
                 basin_file_path=None, basin_color_mapper=None):
        self.basin_file_path = basin_file_path
        self.basin_color_mapper = basin_color_mapper
        self.mask = mask
        self.resolution = resolution
        self.text = text
        if fig_title:
            self.fig_title = fig_title

        self.map_frame = map_frame or {'lat_min': 53.5, 'lat_max': 66.,
                                       'lon_min': 9., 'lon_max': 31.}

    def _draw_map(self):
        print('Drawing map...')
        self.map_figure = plt.figure()
        self.map_axes = self.map_figure.add_subplot(111)
        self.plot_type = 'field'

        self.map = Basemap(projection='stere', boundinglat=54, lon_0=14.5, lat_0=60,
                           resolution=self.resolution,
                           area_thresh=1.,
                           llcrnrlat=self.map_frame['lat_min'], urcrnrlat=self.map_frame['lat_max'],
                           llcrnrlon=self.map_frame['lon_min'], urcrnrlon=self.map_frame['lon_max'],
                           ax=self.map_axes)

        import geopandas as gp
        gf = gp.read_file(self.basin_file_path)
        gf = gf.to_crs(epsg=4326)
        gf = gf.explode()
        for basin, basin_item in self.basin_color_mapper.items():
            basin_boolean = gf['POLY_NAMN'] == basin
            if basin_boolean.any():
                row_geom = gf.loc[basin_boolean, :].iloc[0]
                x, y = self.map(row_geom.geometry.exterior.coords.xy[0],
                                row_geom.geometry.exterior.coords.xy[1])
                poly = Polygon(
                    np.array([x, y]).T,
                    facecolor=basin_item.get('color'),
                    label=basin_item.get('label'),
                    edgecolor='w',
                    zorder=4,
                    linewidth=0.
                )
                self.map_axes.add_patch(poly)

        self.map.drawmapboundary(fill_color='#DEFEFF')
        gf = gp.read_file(gshhs_coastline_path())
        for i, row_geom in gf.iterrows():
            if row_geom['class'] == 4:
                continue
            x, y = self.map(row_geom['geometry'].exterior.coords.xy[0],
                            row_geom['geometry'].exterior.coords.xy[1])
            poly = Polygon(
                np.array([x, y]).T,
                facecolor='w',
                edgecolor='w',
                zorder=3,
                linewidth=0.
            )
            self.map_axes.add_patch(poly)
        self.map.drawcoastlines(linewidth=0.25)
        self.map.drawcountries(linewidth=0.15)
        self.map.fillcontinents(color='w')
        self.map_axes.spines['right'].set_color('white')
        self.map_axes.spines['left'].set_color('white')
        self.map_axes.spines['top'].set_color('white')
        self.map_axes.spines['bottom'].set_color('white')
        self.map_axes.spines['right'].set_visible(False)
        self.map_axes.spines['left'].set_visible(False)
        self.map_axes.spines['top'].set_visible(False)
        self.map_axes.spines['bottom'].set_visible(False)
        plt.legend(loc='upper left', fontsize=9, frameon=False)

    def plot_patches(self, patches):
        """
        :return:
        """
        if any(patches):
            self.map_axes.add_collection(PatchCollection(patches, match_original=True))

    def hide_axis(self):
        plt.axis('off')

    def _save_figure(self, name='test_png_i.png'):
        plt.tight_layout()
        plt.savefig(name, bbox_inches='tight', dpi=600)
        plt.close()


def drawframe(llc_x=9., lrc_x=31., ulc_y=66., llc_y=53.5,
              # llc_x=7., lrc_x=31., ulc_y=66., llc_y=53.,
              framethickness_lat=0.1, framethickness_lon=0.2,
              y_delta=2, x_delta=4,
              BaseMap=None,  # Basemap object
              ax=None):
    # --------------------------------------------------------------------------
    def get_fixed_pos(i, p1, p2, thickness, length_array=None):
        if i == 0:
            return [p1, p1 - thickness, p2, p2]
        elif i + 2 == length_array:
            return [p1, p1, p2 + thickness, p2]
        else:
            return [p1, p1, p2, p2]

    # --------------------------------------------------------------------------
    def cover_patch(x_array, y_array, color='w', ec='w', spaces=20):
        x_array.append(x_array[0])
        y_array.append(y_array[0])

        lons = []
        lats = []
        for i in range(len(x_array) - 1):
            xes = np.linspace(x_array[i], x_array[i + 1], spaces)
            lons.extend(xes)

            yes = np.linspace(y_array[i], y_array[i + 1], spaces)
            lats.extend(yes)

        x, y = BaseMap(lons, lats)
        xy = np.array([x, y]).T

        poly = Polygon(xy, facecolor=color, edgecolor=ec, zorder=4, linewidth=.5)
        ax.add_patch(poly)

    # --------------------------------------------------------------------------
    """ Cover map with patches """
    # Left side
    cover_patch([llc_x - 0.2, llc_x - 30, llc_x - 0.2],
                [ulc_y + 10, ulc_y + 3, llc_y - 3])

    # Right side
    cover_patch([lrc_x + 0.2, lrc_x + 10, lrc_x + 0.2],
                [ulc_y + 10, ulc_y + 3, llc_y - 3])

    # Bottom side
    cover_patch([llc_x - 2, llc_x - 2, lrc_x + 2, lrc_x + 2],
                [llc_y, llc_y - 4, llc_y - 4, llc_y])

    # Top side
    cover_patch([llc_x - 2, llc_x - 2, lrc_x + 2, lrc_x + 2],
                [ulc_y, ulc_y + 4, ulc_y + 4, ulc_y])

    """ Add a black and white frame to our tilted and curved axes """
    if int(llc_y) == llc_y:
        new_parallels = np.arange(llc_y, ulc_y, y_delta / 2.)
        new_parallels = np.append(new_parallels, ulc_y)
    else:
        new_parallels = np.arange(np.ceil(llc_y), ulc_y, y_delta / 2.)
        new_parallels = np.append(new_parallels, ulc_y)
        new_parallels = np.append(llc_y, new_parallels)

    new_meridians = np.arange(llc_x, lrc_x, x_delta / 2.)
    new_meridians = np.append(new_meridians, lrc_x)
    color_array = ['k', 'w'] * 10

    for i in range(len(new_meridians) - 1):
        # lower frameside
        x = get_fixed_pos(i, new_meridians[i], new_meridians[i + 1],
                          framethickness_lon, length_array=len(new_meridians))
        y = [llc_y, llc_y - framethickness_lat, llc_y - framethickness_lat, llc_y]
        cover_patch(x, y, color=color_array[i], ec='k')

        # upper frameside
        x = get_fixed_pos(i, new_meridians[i], new_meridians[i + 1],
                          framethickness_lon, length_array=len(new_meridians))
        y = [ulc_y, ulc_y + framethickness_lat, ulc_y + framethickness_lat, ulc_y]
        cover_patch(x, y, color=color_array[i + 1], ec='k')

    for i in range(len(new_parallels) - 1):
        # right frameside
        x = [lrc_x, lrc_x + framethickness_lon, lrc_x + framethickness_lon, lrc_x]
        y = get_fixed_pos(i, new_parallels[i], new_parallels[i + 1],
                          framethickness_lat, length_array=len(new_parallels))
        cover_patch(x, y, color=color_array[i], ec='k')

        # left frameside
        x = [llc_x, llc_x - framethickness_lon, llc_x - framethickness_lon, llc_x]
        y = get_fixed_pos(i, new_parallels[i], new_parallels[i + 1],
                          framethickness_lat, length_array=len(new_parallels))
        cover_patch(x, y, color=color_array[i + 1], ec='k')

    # Y-Labels
    for lat in np.arange(llc_y+1.5, ulc_y, y_delta):
        adjustment = 1. / (ulc_y / lat) ** 2
        tx, ty = BaseMap(llc_x - adjustment, lat)
        plt.text(tx, ty, str(lat).replace('.0', '') + '$^{o}$N',
                 fontsize=11,
                 ha='right',
                 va='center',
                 color='k',
                 zorder=5)

    # X-Labels
    for lon in np.arange(llc_x+2, lrc_x + x_delta, x_delta):
        adjustment = 0.4
        tx, ty = BaseMap(lon, llc_y - adjustment)
        plt.text(tx, ty, str(lon).replace('.0', '') + '$^{o}$E',
                 fontsize=11,
                 ha='center',
                 va='top',
                 color='k',
                 zorder=5)
