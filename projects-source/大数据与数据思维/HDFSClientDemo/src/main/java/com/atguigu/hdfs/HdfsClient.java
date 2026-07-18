package com.atguigu.hdfs;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.*;
import org.apache.hadoop.io.IOUtils;
import org.junit.Test;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.net.URI;

public class HdfsClient {

    // 1. 创建目录
    @Test
    public void testMkdirs() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(
                new URI("hdfs://192.168.88.100:9000"),
                conf,
                "root"
        );

        fs.mkdirs(new Path("/test/hdfs/demo"));
        fs.close();
        System.out.println("目录创建成功");
    }

    // 2. 文件上传
    @Test
    public void testUpload() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        fs.copyFromLocalFile(
                new Path("D:/test.txt"),
                new Path("/test/hdfs/demo/test.txt")
        );

        fs.close();
        System.out.println("上传成功");
    }

    //2.1参数优先级测试
    @Test
    public void testUploadWithPriority() throws Exception {
        Configuration conf = new Configuration();
        // 代码中设置副本数为2（优先级最高）
        conf.set("dfs.replication", "2");
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        fs.copyFromLocalFile(new Path("D:/test.txt"), new Path("/test/hdfs/demo/priority_test.txt"));
        fs.close();
        System.out.println("上传完成，请到Web UI查看副本数，应为2");
    }

    // 3. 文件下载
    @Test
    public void testDownload() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        fs.copyToLocalFile(
                false,
                new Path("/test/hdfs/demo/test.txt"),
                new Path("D:/download.txt"),
                true
        );

        fs.close();
        System.out.println("下载成功");
    }


    // 4. 查看文件详情（文件名、大小、权限、所有者）
    @Test
    public void testListFiles() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        // 递归获取目录下所有文件信息
        RemoteIterator<LocatedFileStatus> listFiles = fs.listFiles(new Path("/test/hdfs/demo"), true);

        while (listFiles.hasNext()) {
            LocatedFileStatus file = listFiles.next();
            System.out.println("==================== 文件信息 ====================");
            System.out.println("文件路径：" + file.getPath());
            System.out.println("文件名称：" + file.getPath().getName());
            System.out.println("文件大小：" + file.getLen() + " 字节");
            System.out.println("文件权限：" + file.getPermission());
            System.out.println("文件所有者：" + file.getOwner());
            System.out.println("==================================================\n");
        }

        fs.close();
    }



    // 5. 文件重命名
    @Test
    public void testRename() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        // 将 test.txt 改名为 new_test.txt
        boolean result = fs.rename(
                new Path("/test/hdfs/demo/test.txt"),
                new Path("/test/hdfs/demo/new_test.txt")
        );

        System.out.println(result ? "重命名成功" : "重命名失败");
        fs.close();
    }

    // 6. IO流方式上传文件（底层流操作）
    @Test
    public void testUploadByIO() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        // 本地文件输入流
        FileInputStream in = new FileInputStream("D:/test.txt");
        // HDFS输出流
        FSDataOutputStream out = fs.create(new Path("/test/hdfs/demo/io_upload.txt"));

        // 流拷贝
        IOUtils.copyBytes(in, out, conf);

        // 关闭流
        IOUtils.closeStream(in);
        IOUtils.closeStream(out);
        fs.close();

        System.out.println("IO流上传成功");
    }

    // 7. IO流方式下载文件
    @Test
    public void testDownloadByIO() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        // HDFS输入流
        FSDataInputStream in = fs.open(new Path("/test/hdfs/demo/io_upload.txt"));
        // 本地输出流
        FileOutputStream out = new FileOutputStream("D:/io_download.txt");

        // 流拷贝
        IOUtils.copyBytes(in, out, conf);

        // 关闭流
        IOUtils.closeStream(in);
        IOUtils.closeStream(out);
        fs.close();

        System.out.println("IO流下载成功");
    }

    // 8.1 读取第一块数据（前 128MB）
    @Test
    public void testReadFileSeek1() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        // 打开HDFS输入流
        FSDataInputStream fis = fs.open(new Path("/test/hdfs/demo/test.txt"));
        // 本地输出流：写入第一块
        FileOutputStream fos = new FileOutputStream("D:/test.txt.part1");

        // 只拷贝前 128MB 数据
        byte[] buf = new byte[1024];
        for (int i = 0; i < 1024 * 128; i++) {
            fis.read(buf);
            fos.write(buf);
        }

        IOUtils.closeStream(fos);
        IOUtils.closeStream(fis);
        fs.close();
        System.out.println("第一块读取成功");
    }

    // 8.2 读取第二块数据（从 128MB 位置开始）（可选）
    @Test
    public void testReadFileSeek2() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        FSDataInputStream fis = fs.open(new Path("/test/hdfs/demo/test.txt"));
        FileOutputStream fos = new FileOutputStream("D:/test.txt.part2");

        // 定位到 128MB 位置
        fis.seek(1024 * 1024 * 128);
        IOUtils.copyBytes(fis, fos, conf);

        IOUtils.closeStream(fos);
        IOUtils.closeStream(fis);
        fs.close();
        System.out.println("第二块读取成功");
    }

    // 9. 文件和文件夹判断（展示根目录下哪些是文件，哪些是目录）
    @Test
    public void testListStatus() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        FileStatus[] statuses = fs.listStatus(new Path("/"));
        System.out.println("===== 根目录下文件和目录判断 =====");
        for (FileStatus status : statuses) {
            if (status.isFile()) {
                System.out.println("文件：" + status.getPath().getName());
            } else {
                System.out.println("目录：" + status.getPath().getName());
            }
        }
        fs.close();
    }

    // 10. 文件详情查看（含数据块所在主机信息）
    @Test
    public void testFileDetailWithBlocks() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        RemoteIterator<LocatedFileStatus> listFiles = fs.listFiles(new Path("/test/hdfs/demo"), true);
        System.out.println("===== 文件详情（含块信息） =====");
        while (listFiles.hasNext()) {
            LocatedFileStatus status = listFiles.next();
            System.out.println("文件路径：" + status.getPath());
            System.out.println("文件名称：" + status.getPath().getName());
            System.out.println("文件大小：" + status.getLen() + " 字节");
            System.out.println("权限：" + status.getPermission());
            System.out.println("所有者：" + status.getOwner());

           //输出块信息
            BlockLocation[] blockLocations = status.getBlockLocations();
            for (BlockLocation blk : blockLocations) {
                System.out.println("  块偏移：" + blk.getOffset() +
                        "，块长度：" + blk.getLength());
                System.out.println("  所在主机：" + String.join(",", blk.getHosts()));
            }
            System.out.println("------------------------------------");
        }
        fs.close();
    }

    // 11. 删除目录
    @Test
    public void testDelete() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        fs.delete(new Path("/test/hdfs/demo"), true);
        fs.close();
        System.out.println("删除成功");
    }


}
